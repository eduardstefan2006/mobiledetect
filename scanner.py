async def scan_once(scanner: MikroTikScanner) -> None:
    results = await scanner.collect_all()
    process_scan_results(results)


async def scanner_loop() -> None:
    scanner = MikroTikScanner()
    while True:
        try:
            await scan_once(scanner)
        except Exception as exc:
            logger.exception("Scan cycle failed: %s", exc)
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)