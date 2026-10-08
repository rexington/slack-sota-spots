import csv
import io
import unittest

from slack_callsigns import base_callsign, extract_callsign, parse_members


class ExtractCallsignTest(unittest.TestCase):
    def test_finds_callsign(self):
        cases = {
            "Rex VE7XXX": "VE7XXX",
            "ve7xxx - Rex": "VE7XXX",
            "Rex (W1ABC)": "W1ABC",
            "KD0XYZ/P": "KD0XYZ",
            "VE7/W1ABC": "W1ABC",
            "W6/KD0XYZ/P": "KD0XYZ",
            "Jane Doe | AB1CD": "AB1CD",
            "Bob – N6AAA": "N6AAA",
            "4X4ABC": "4X4ABC",
            "Sam [K7SAM]": "K7SAM",
            "Sam K7SAM ex KD0XYZ": "K7SAM",
            "K7SAM, Sam": "K7SAM",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(extract_callsign(name), expected)

    def test_no_callsign(self):
        for name in ["John Smith", "4x4", "2FA", "MP3", "COVID19", "", None]:
            with self.subTest(name=name):
                self.assertIsNone(extract_callsign(name))

    def test_base_callsign(self):
        self.assertEqual(base_callsign("ve7/w1abc/qrp"), "W1ABC")
        self.assertIsNone(base_callsign("hello"))


class ParseMembersTest(unittest.TestCase):
    def parse(self, text):
        reader = csv.DictReader(io.StringIO(text))
        return parse_members(reader, reader.fieldnames)

    def test_slack_export(self):
        text = (
            "username,email,status,fullname,displayname\n"
            "rex,a@x,Admin,Rex Smith,Rex VE7XXX\n"
            "jane,b@x,Member,Jane AB1CD,\n"
            "old,c@x,Deactivated,Old W1OLD,W1OLD\n"
            "bot,d@x,Bot,Spot Bot,K1BOT\n"
            "pat,e@x,Member,Pat Jones,pat\n"
        )
        callsigns, missing, members = self.parse(text)
        self.assertEqual(callsigns, {"VE7XXX", "AB1CD"})
        self.assertEqual(missing, ["pat"])
        self.assertEqual(members, 3)

    def test_only_active_members(self):
        text = (
            "username,billing-active,fullname,displayname\n"
            "rex,1,Rex Smith,Rex VE7XXX\n"
            "sam,0,Sam,K7SAM\n"
            "pat,1,Pat Jones,pat\n"
        )
        callsigns, missing, members = self.parse(text)
        self.assertEqual(callsigns, {"VE7XXX"})
        self.assertEqual(missing, ["pat"])
        self.assertEqual(members, 2)

    def test_missing_columns(self):
        with self.assertRaises(ValueError):
            self.parse("username,email\nrex,a@x\n")


if __name__ == "__main__":
    unittest.main()
