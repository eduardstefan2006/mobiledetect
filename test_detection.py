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

    def test_explicitly_excludes_non_mobile_hostname(self) -> None:
        self.assertFalse(is_phone_device("lab-printer-01", "Apple"))

    def test_detects_phone_from_randomized_mac_when_hostname_and_vendor_missing(self) -> None:
        self.assertTrue(is_phone_device(None, None, "02:11:22:33:44:55"))

    def test_does_not_detect_phone_from_globally_administered_mac_without_other_signals(self) -> None:
        self.assertFalse(is_phone_device(None, None, "00:11:22:33:44:55"))


if __name__ == "__main__":
    unittest.main()
