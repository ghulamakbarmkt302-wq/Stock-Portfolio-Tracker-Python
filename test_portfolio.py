import csv, io, os, sys, tempfile, unittest, contextlib, builtins
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portfolio as pf

class T(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
    def write(self, name, text):
        p = os.path.join(self.dir, name)
        with open(p, "w", encoding="utf-8") as f: f.write(text)
        return p

    def test_load_prices_uses_last_row_per_symbol(self):
        p = self.write("p.csv", "Date,Symbol,Close\n2026-01-01,aapl,100\n2026-01-02,AAPL,110\n2026-01-02,MSFT,300\n")
        self.assertEqual(pf.load_prices(p), {"AAPL": 110.0, "MSFT": 300.0})

    def test_load_prices_price_column_and_bad_rows(self):
        p = self.write("p.csv", "Symbol,Price\nAAPL,50\nBAD,abc\nZERO,0\n")
        self.assertEqual(pf.load_prices(p), {"AAPL": 50.0})

    def test_load_prices_missing_symbol_column(self):
        p = self.write("p.csv", "Ticker,Close\nAAPL,1\n")
        with self.assertRaises(ValueError): pf.load_prices(p)

    def test_load_prices_missing_price_column(self):
        p = self.write("p.csv", "Symbol,Volume\nAAPL,1\n")
        with self.assertRaises(ValueError): pf.load_prices(p)

    def test_add_position_averages_cost(self):
        port = {}
        pf.add_position(port, "aapl", 10, 100)
        pos = pf.add_position(port, "AAPL", 10, 200)
        self.assertEqual(pos["shares"], 20)
        self.assertAlmostEqual(pos["buy_price"], 150)

    def test_add_position_validation(self):
        port = {}
        for args in [("", 1, 1), ("X", 0, 1), ("X", 1, 0), ("X", -2, 5)]:
            with self.assertRaises(ValueError): pf.add_position(port, *args)
        self.assertEqual(port, {})

    def test_value_positions_gain_and_missing(self):
        port = {"AAPL": {"shares": 10, "buy_price": 100.0}, "NOPE": {"shares": 1, "buy_price": 5.0}}
        rows, missing = pf.value_positions(port, {"AAPL": 120.0})
        self.assertEqual(missing, ["NOPE"])
        r = rows[0]
        self.assertEqual(r["invested"], 1000); self.assertEqual(r["current_value"], 1200)
        self.assertEqual(r["gain_loss"], 200); self.assertAlmostEqual(r["gain_loss_pct"], 20.0)

    def test_totals_and_loss(self):
        port = {"A": {"shares": 1, "buy_price": 100.0}, "B": {"shares": 2, "buy_price": 50.0}}
        rows, _ = pf.value_positions(port, {"A": 80.0, "B": 60.0})
        t = pf.totals(rows)
        self.assertEqual(t["invested"], 200); self.assertEqual(t["current_value"], 200)
        self.assertEqual(t["gain_loss"], 0)
        rows, _ = pf.value_positions({"A": {"shares": 1, "buy_price": 100.0}}, {"A": 75.0})
        self.assertAlmostEqual(pf.totals(rows)["gain_loss_pct"], -25.0)

    def test_save_summary_appends_with_one_header(self):
        port = {"A": {"shares": 1, "buy_price": 10.0}}
        rows, _ = pf.value_positions(port, {"A": 12.0})
        path = os.path.join(self.dir, "s.csv")
        pf.save_summary(path, rows, "2026-10-21 10:00:00")
        pf.save_summary(path, rows, "2026-10-21 11:00:00")
        with open(path, newline="") as f: data = list(csv.reader(f))
        self.assertEqual(data[0], pf.SUMMARY_FIELDS)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[1][0], "2026-10-21 10:00:00")
        self.assertEqual(data[2][0], "2026-10-21 11:00:00")

    def test_format_table_has_total_line(self):
        rows, _ = pf.value_positions({"A": {"shares": 1, "buy_price": 10.0}}, {"A": 12.0})
        out = pf.format_table(rows)
        self.assertIn("TOTAL", out); self.assertIn("+20.00", out)

    def test_full_session_via_menu(self):
        prices = self.write("p.csv", "Date,Symbol,Close\n2026-10-21,AAPL,120\n")
        summary = os.path.join(self.dir, "sum.csv")
        inputs = iter(["1", "AAPL", "10", "100", "2", "3", "9", "4"])
        orig = builtins.input; builtins.input = lambda p="": next(inputs)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                pf.main(["--prices", prices, "--summary", summary])
        finally:
            builtins.input = orig
        out = buf.getvalue()
        self.assertIn("Saved AAPL", out); self.assertIn("Saved 1 rows", out)
        self.assertIn("Please choose 1, 2, 3 or 4.", out); self.assertIn("TOTAL", out)
        self.assertTrue(os.path.exists(summary))

    def test_missing_price_file_still_runs(self):
        inputs = iter(["4"])
        orig = builtins.input; builtins.input = lambda p="": next(inputs)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                pf.main(["--prices", "/nonexistent.csv"])
        finally:
            builtins.input = orig
        self.assertIn("not found", buf.getvalue()); self.assertIn("Goodbye", buf.getvalue())

if __name__ == "__main__":
    unittest.main(verbosity=1)
