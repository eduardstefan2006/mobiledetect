import unittest

from detection import is_phone_device


class IsPhoneDeviceTests(unittest.TestCase):
    def test_detects_phone_from_hostname(self) -> None:
        self.assertTrue(is_phone_device("my-iphone", None))

    def test_detects_tablet_as_mobile_device(self) -> None:
        self.assertTrue(is_phone_device("office-ipad", None))

    def test_detects_smartwatch_as_mobile_device(self) -> None:
        self.assertTrue(is_phone_device("garmin-watch", None))

    def test_detects_phone_from_vendor(self) -> None:
        self.assertTrue(is_phone_device(None, "Google LLC"))

    def test_detects_mobile_vendor_from_extended_keywords(self) -> None:
        self.assertTrue(is_phone_device(None, "Fitbit Inc"))

    def test_does_not_detect_laptop_vendors_as_mobile(self) -> None:
        self.assertFalse(is_phone_device(None, "ASUSTeK"))
        self.assertFalse(is_phone_device(None, "Lenovo Group"))
        self.assertFalse(is_phone_device(None, "Acer Inc"))

    def test_explicitly_excludes_non_mobile_hostname(self) -> None:
        self.assertFalse(is_phone_device("lab-printer-01", "Apple"))

    def test_does_not_detect_common_laptop_hostnames_as_mobile(self) -> None:
        self.assertFalse(is_phone_device("macbook-office", None))
        self.assertFalse(is_phone_device("office-vivobook-a14", None))
        self.assertFalse(is_phone_device("teacher-thinkpad", "Lenovo"))
        self.assertFalse(is_phone_device("student-macbook-air", "Apple"))
        self.assertFalse(is_phone_device("classroom-chromebook-12", "Google"))

    def test_does_not_detect_printer_brand_hostname_as_mobile(self) -> None:
        self.assertFalse(is_phone_device("Canon71a541", None))
        self.assertFalse(is_phone_device("epson-office-01", "Epson"))

    def test_does_not_detect_phone_from_randomized_mac_when_hostname_and_vendor_missing(self) -> None:
        self.assertFalse(is_phone_device(None, None, "02:11:22:33:44:55"))

    def test_does_not_detect_infrastructure_hostname_with_randomized_mac(self) -> None:
        self.assertFalse(is_phone_device("PiHole", None, "a2:80:54:05:4f:02"))
        self.assertFalse(is_phone_device("ResurseUmane", None, "46:b7:3b:71:b9:ef"))

    def test_does_not_detect_randomized_mac_with_non_mobile_hostname(self) -> None:
        self.assertFalse(is_phone_device("server-ubuntu", None, "02:11:22:33:44:55"))

    def test_does_not_detect_randomized_mac_with_non_mobile_vendor(self) -> None:
        self.assertFalse(is_phone_device(None, "Cisco Systems", "02:11:22:33:44:55"))

    def test_does_not_detect_phone_from_randomized_mac_with_blank_hostname_and_vendor(self) -> None:
        self.assertFalse(is_phone_device("   ", "   ", "02:11:22:33:44:55"))

    def test_does_not_detect_phone_from_randomized_mac_with_empty_hostname_and_vendor(self) -> None:
        self.assertFalse(is_phone_device("", "", "02:11:22:33:44:55"))

    def test_does_not_detect_phone_from_globally_administered_mac_without_other_signals(self) -> None:
        self.assertFalse(is_phone_device(None, None, "00:11:22:33:44:55"))


if __name__ == "__main__":
    unittest.main()
