from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import librouteros

app = FastAPI(title="Network Monitor API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:secure_pass@localhost/network_monitor")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    mac_address = Column(String, primary_key=True)
    ip_address = Column(String)
    name = Column(String)
    is_mobile = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# Routes
@app.get("/health")
async def health():
    return {"status": "ok", "service": "network-monitor-api"}

@app.get("/api/devices")
async def list_devices():
    db = SessionLocal()
    try:
        devices = db.query(Device).all()
        return [
            {
                "mac": d.mac_address,
                "ip": d.ip_address,
                "name": d.name,
                "is_mobile": d.is_mobile,
                "last_seen": d.last_seen.isoformat()
            }
            for d in devices
        ]
    finally:
        db.close()

@app.get("/api/devices/{mac}")
async def get_device(mac: str):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.mac_address == mac).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return {
            "mac": device.mac_address,
            "ip": device.ip_address,
            "name": device.name,
            "is_mobile": device.is_mobile,
            "last_seen": device.last_seen.isoformat()
        }
    finally:
        db.close()

@app.post("/api/devices/scan")
async def scan_devices():
    """Scan Mikrotik și actualizează dispozitivele"""
    host = os.getenv("MIKROTIK_HOST")
    user = os.getenv("MIKROTIK_USER")
    password = os.getenv("MIKROTIK_PASS")
    
    try:
        conn = librouteros.connect(host, user, password)
        interfaces = conn(cmd='.ip.arp.print', arguments={})
        
        db = SessionLocal()
        for entry in interfaces:
            mac = entry['.id']
            device = db.query(Device).filter(Device.mac_address == mac).first()
            if not device:
                device = Device(mac_address=mac)
            
            device.ip_address = entry.get('address', '')
            device.last_seen = datetime.utcnow()
            db.add(device)
        
        db.commit()
        db.close()
        conn.close()
        
        return {"status": "scan_complete", "devices_updated": len(interfaces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
