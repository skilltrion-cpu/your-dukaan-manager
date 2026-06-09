import sys, os, sqlite3, shutil
from datetime import datetime, date
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QStackedWidget,
    QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox, QComboBox,
    QTextEdit, QFrame, QFileDialog, QCheckBox, QDialog, QFormLayout,
    QInputDialog, QDateEdit
)
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtGui import QFont, QPixmap, QIcon

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None

APP_NAME = "Your Dukaan Manager"
APP_VERSION = "3.0.0"
DB_FILE = "your_dukaan_manager.db"
ICON_FILE = "desktop logo.ico"
BANNER_FILE = "login screen banner.png"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.migrate_tables()
        self.create_default_settings()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,nickname TEXT,dob TEXT,created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS shop_settings(id INTEGER PRIMARY KEY CHECK(id=1),shop_name TEXT,business_name TEXT,gst_number TEXT,address TEXT,phone TEXT,logo_path TEXT,gst_enabled INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,purchase_price REAL DEFAULT 0,selling_price REAL DEFAULT 0,stock INTEGER DEFAULT 0,low_stock_limit INTEGER DEFAULT 5,gst_percent REAL DEFAULT 0,created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,phone TEXT,alt_phone TEXT,company_name TEXT,gst_number TEXT,address TEXT,city_area TEXT,landmark TEXT,notes TEXT,discount_percent REAL DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,phone TEXT,address TEXT,gst_number TEXT,notes TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY AUTOINCREMENT,bill_no TEXT,date TEXT,customer_id INTEGER,customer_name TEXT,company_name TEXT,subtotal REAL,gst_amount REAL,discount REAL,discount_percent REAL DEFAULT 0,grand_total REAL,payment_mode TEXT,gross_profit REAL DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sale_items(id INTEGER PRIMARY KEY AUTOINCREMENT,sale_id INTEGER,product_id INTEGER,product_name TEXT,qty INTEGER,purchase_price REAL DEFAULT 0,price REAL,gst_percent REAL,discount_percent REAL DEFAULT 0,total REAL,profit REAL DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT,amount REAL,category TEXT,description TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY AUTOINCREMENT,purchase_no TEXT,date TEXT,supplier_id INTEGER,supplier_name TEXT,subtotal REAL,gst_amount REAL DEFAULT 0,other_charges REAL DEFAULT 0,grand_total REAL,payment_mode TEXT,notes TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS purchase_items(id INTEGER PRIMARY KEY AUTOINCREMENT,purchase_id INTEGER,product_id INTEGER,product_name TEXT,qty INTEGER,purchase_price REAL,gst_percent REAL DEFAULT 0,total REAL)''')
        self.conn.commit()

    def migrate_tables(self):
        migrations = {
            "users": {"nickname": "TEXT", "dob": "TEXT"},
            "customers": {"alt_phone": "TEXT", "gst_number": "TEXT", "city_area": "TEXT", "landmark": "TEXT", "notes": "TEXT", "discount_percent": "REAL DEFAULT 0"},
            "suppliers": {"gst_number": "TEXT", "notes": "TEXT"},
            "sales": {"customer_id": "INTEGER", "discount_percent": "REAL DEFAULT 0", "gross_profit": "REAL DEFAULT 0"},
            "sale_items": {"purchase_price": "REAL DEFAULT 0", "discount_percent": "REAL DEFAULT 0", "profit": "REAL DEFAULT 0"}
        }
        for table, cols in migrations.items():
            existing = [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
            for col, spec in cols.items():
                if col not in existing:
                    try:
                        self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {spec}")
                    except Exception:
                        pass
        self.conn.commit()

    def create_default_settings(self):
        if self.fetchone("SELECT COUNT(*) c FROM shop_settings")["c"] == 0:
            self.execute('''INSERT INTO shop_settings(id,shop_name,business_name,gst_number,address,phone,logo_path,gst_enabled) VALUES(1,'Your Dukaan','Your Business Name','','Your Address','9999999999','',0)''')

    def execute(self, query, params=()):
        cur = self.conn.cursor(); cur.execute(query, params); self.conn.commit(); return cur
    def fetchall(self, query, params=()): return self.conn.execute(query, params).fetchall()
    def fetchone(self, query, params=()): return self.conn.execute(query, params).fetchone()

db = Database()

STYLE = '''
QMainWindow, QWidget { background:#101827; color:#F8FAFC; font-family:Segoe UI; }
QLineEdit,QComboBox,QTextEdit,QSpinBox,QDoubleSpinBox,QDateEdit { background:#1E293B; color:white; border:1px solid #334155; border-radius:8px; padding:8px; font-size:13px; }
QPushButton { background:#16A34A; color:white; border:none; border-radius:10px; padding:10px 14px; font-weight:bold; }
QPushButton:hover { background:#22C55E; }
QPushButton#danger { background:#DC2626; }
QPushButton#blue { background:#2563EB; }
QPushButton#orange { background:#F97316; }
QPushButton#side { background:transparent; text-align:left; padding:14px; border-radius:8px; font-size:14px; }
QPushButton#side:hover { background:#1E293B; }
QTableWidget { background:#0F172A; color:white; gridline-color:#334155; border:1px solid #334155; }
QHeaderView::section { background:#1E293B; color:white; padding:8px; border:none; }
QFrame#card { background:#1E293B; border-radius:16px; border:1px solid #334155; }
QLabel#muted { color:#94A3B8; }
'''

def title_label(text, size=22):
    label = QLabel(text); label.setFont(QFont("Segoe UI", size, QFont.Bold)); return label

def make_card(title, value):
    card = QFrame(); card.setObjectName("card"); lay = QVBoxLayout(card)
    t = QLabel(title); t.setObjectName("muted")
    v = QLabel(str(value)); v.setFont(QFont("Segoe UI", 20, QFont.Bold)); v.setStyleSheet("color:#22C55E;")
    lay.addWidget(t); lay.addWidget(v); return card

def set_table(table, headers, rows):
    table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers); table.setRowCount(0)
    for r in rows:
        row = table.rowCount(); table.insertRow(row)
        for col, val in enumerate(r): table.setItem(row, col, QTableWidgetItem(str(val)))
    table.resizeColumnsToContents()

def asset_icon(name): return QIcon(name) if Path(name).exists() else QIcon()
def money(v):
    try: return f"₹{float(v):.2f}"
    except Exception: return "₹0.00"

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Create Account"); self.setMinimumWidth(420)
        lay = QVBoxLayout(self); form = QFormLayout()
        self.email = QLineEdit(); self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password)
        self.nickname = QLineEdit(); self.nickname.setPlaceholderText("Used for password reset")
        self.dob = QDateEdit(); self.dob.setCalendarPopup(True); self.dob.setDisplayFormat("yyyy-MM-dd"); self.dob.setDate(QDate(2000,1,1))
        form.addRow("Email", self.email); form.addRow("Password", self.password); form.addRow("Your Nick Name", self.nickname); form.addRow("Date of Birth", self.dob)
        save = QPushButton("Create Account"); save.clicked.connect(self.accept)
        lay.addLayout(form); lay.addWidget(save)

class LoginPage(QWidget):
    def __init__(self, app_window): super().__init__(); self.app_window = app_window; self.build_ui()
    def build_ui(self):
        root = QVBoxLayout(self); root.setAlignment(Qt.AlignCenter)
        box = QFrame(); box.setObjectName("card"); box.setFixedWidth(480); form = QVBoxLayout(box); form.setSpacing(12)
        if Path(BANNER_FILE).exists():
            banner = QLabel(); pix = QPixmap(BANNER_FILE); banner.setPixmap(pix.scaled(430, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation)); banner.setAlignment(Qt.AlignCenter); form.addWidget(banner)
        title = title_label("Your Dukaan Manager", 24); title.setAlignment(Qt.AlignCenter)
        sub = QLabel("Smart Billing • Inventory • Profit Tracking"); sub.setAlignment(Qt.AlignCenter); sub.setObjectName("muted")
        self.email = QLineEdit(); self.email.setPlaceholderText("Email")
        self.password = QLineEdit(); self.password.setPlaceholderText("Password"); self.password.setEchoMode(QLineEdit.Password)
        login = QPushButton("Login"); login.clicked.connect(self.login)
        reg = QPushButton("Create New Account"); reg.setObjectName("blue"); reg.clicked.connect(self.register)
        forgot = QPushButton("Forgot Password / Secure Reset"); forgot.setObjectName("orange"); forgot.clicked.connect(self.forgot_password)
        form.addWidget(title); form.addWidget(sub); form.addWidget(self.email); form.addWidget(self.password); form.addWidget(login); form.addWidget(reg); form.addWidget(forgot); root.addWidget(box)
    def login(self):
        u = db.fetchone("SELECT * FROM users WHERE email=? AND password=?", (self.email.text().strip(), self.password.text().strip()))
        if u: self.app_window.show_main_app()
        else: QMessageBox.warning(self, "Login Failed", "Invalid email or password")
    def register(self):
        d = RegisterDialog(self)
        if d.exec() == QDialog.Accepted:
            email, pw, nick, dob = d.email.text().strip(), d.password.text().strip(), d.nickname.text().strip().lower(), d.dob.date().toString("yyyy-MM-dd")
            if not email or not pw or not nick: QMessageBox.warning(self, "Required", "Email, password, nickname and DOB required"); return
            try:
                db.execute("INSERT INTO users(email,password,nickname,dob,created_at) VALUES(?,?,?,?,?)", (email, pw, nick, dob, datetime.now().isoformat()))
                QMessageBox.information(self, "Success", "Account created. Now login.")
            except sqlite3.IntegrityError: QMessageBox.warning(self, "Exists", "This email is already registered")
    def forgot_password(self):
        email = self.email.text().strip()
        if not email: QMessageBox.warning(self, "Email Required", "Enter registered email first."); return
        user = db.fetchone("SELECT * FROM users WHERE email=?", (email,))
        if not user: QMessageBox.warning(self, "Not Found", "This email is not registered."); return
        nick, ok = QInputDialog.getText(self, "Security Question 1", "Your nick name?")
        if not ok: return
        dob, ok = QInputDialog.getText(self, "Security Question 2", "Date of birth? Format: yyyy-mm-dd")
        if not ok: return
        if (nick.strip().lower() == (user["nickname"] or "").lower()) and (dob.strip() == (user["dob"] or "")):
            new_pw, ok = QInputDialog.getText(self, "Reset Password", "Enter new password:")
            if ok and new_pw.strip(): db.execute("UPDATE users SET password=? WHERE email=?", (new_pw.strip(), email)); QMessageBox.information(self, "Done", "Password reset successfully.")
        else: QMessageBox.warning(self, "Wrong Answer", "Security answers do not match.")

class DashboardPage(QWidget):
    def __init__(self): super().__init__(); self.layout = QVBoxLayout(self); self.build_ui()
    def build_ui(self):
        if Path(BANNER_FILE).exists():
            banner = QLabel(); pix = QPixmap(BANNER_FILE); banner.setPixmap(pix.scaled(850, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)); banner.setAlignment(Qt.AlignCenter); self.layout.addWidget(banner)
        self.layout.addWidget(title_label("Dashboard")); self.cards = QGridLayout(); self.layout.addLayout(self.cards)
        self.alert = QTextEdit(); self.alert.setReadOnly(True); self.alert.setFixedHeight(150); self.layout.addWidget(QLabel("Stock Alerts")); self.layout.addWidget(self.alert); self.refresh()
    def refresh(self):
        while self.cards.count():
            w = self.cards.takeAt(0).widget()
            if w: w.deleteLater()
        today, month, year = date.today().strftime("%Y-%m-%d"), date.today().strftime("%Y-%m"), date.today().strftime("%Y")
        today_sales = db.fetchone("SELECT COALESCE(SUM(grand_total),0) v FROM sales WHERE date=?", (today,))["v"]
        today_exp = db.fetchone("SELECT COALESCE(SUM(amount),0) v FROM expenses WHERE date=?", (today,))["v"]
        today_pur = db.fetchone("SELECT COALESCE(SUM(grand_total),0) v FROM purchases WHERE date=?", (today,))["v"]
        month_sales = db.fetchone("SELECT COALESCE(SUM(grand_total),0) v FROM sales WHERE substr(date,1,7)=?", (month,))["v"]
        month_pur = db.fetchone("SELECT COALESCE(SUM(grand_total),0) v FROM purchases WHERE substr(date,1,7)=?", (month,))["v"]
        year_sales = db.fetchone("SELECT COALESCE(SUM(grand_total),0) v FROM sales WHERE substr(date,1,4)=?", (year,))["v"]
        profit = db.fetchone("SELECT COALESCE(SUM(gross_profit),0) v FROM sales WHERE date=?", (today,))["v"] - today_exp
        data = [("Today Sales", money(today_sales)), ("Today Purchase", money(today_pur)), ("Today Expenses", money(today_exp)), ("Today Net Profit/Loss", money(profit)), ("Monthly Sales", money(month_sales)), ("Monthly Purchase", money(month_pur)), ("Yearly Sales", money(year_sales)), ("Low Stock", db.fetchone("SELECT COUNT(*) v FROM products WHERE stock<=low_stock_limit AND stock>0")["v"]), ("Out of Stock", db.fetchone("SELECT COUNT(*) v FROM products WHERE stock<=0")["v"])]
        for i,(t,v) in enumerate(data): self.cards.addWidget(make_card(t,v), i//3, i%3)
        rows = db.fetchall("SELECT name,stock,low_stock_limit FROM products WHERE stock<=low_stock_limit ORDER BY stock")
        text = "No low stock alerts." if not rows else ""
        for r in rows: text += f"{'OUT OF STOCK' if r['stock']<=0 else 'LOW STOCK'}: {r['name']} | Stock: {r['stock']} | Alert Limit: {r['low_stock_limit']}\n"
        self.alert.setText(text)

class InventoryPage(QWidget):
    def __init__(self): super().__init__(); self.selected_id = None; self.build_ui(); self.load_products()
    def build_ui(self):
        root = QVBoxLayout(self); root.addWidget(title_label("Inventory Management")); form = QGridLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search product..."); self.search.textChanged.connect(self.load_products)
        self.name = QLineEdit(); self.category = QLineEdit(); self.purchase = QDoubleSpinBox(); self.purchase.setMaximum(999999); self.purchase.setPrefix("₹")
        self.sell = QDoubleSpinBox(); self.sell.setMaximum(999999); self.sell.setPrefix("₹"); self.stock = QSpinBox(); self.stock.setMaximum(999999); self.low = QSpinBox(); self.low.setMaximum(999999); self.low.setValue(5); self.gst = QDoubleSpinBox(); self.gst.setMaximum(100); self.gst.setSuffix("%")
        fields=[("Search",self.search),("Name",self.name),("Category",self.category),("Purchase",self.purchase),("Selling",self.sell),("Stock",self.stock),("Low Alert",self.low),("GST %",self.gst)]
        for i,(lab,w) in enumerate(fields): form.addWidget(QLabel(lab),i//2,i%2*2); form.addWidget(w,i//2,i%2*2+1)
        btns = QHBoxLayout(); add = QPushButton("Add Product"); add.clicked.connect(self.add_product); upd = QPushButton("Update Selected"); upd.setObjectName("blue"); upd.clicked.connect(self.update_product); delete = QPushButton("Delete Selected"); delete.setObjectName("danger"); delete.clicked.connect(self.delete_selected); btns.addWidget(add); btns.addWidget(upd); btns.addWidget(delete)
        self.table = QTableWidget(); self.table.cellClicked.connect(self.pick_product); root.addLayout(form); root.addLayout(btns); root.addWidget(self.table)
    def values(self): return (self.name.text().strip(), self.category.text().strip(), self.purchase.value(), self.sell.value(), self.stock.value(), self.low.value(), self.gst.value())
    def add_product(self):
        if not self.name.text().strip(): QMessageBox.warning(self,"Required","Product name required"); return
        db.execute("INSERT INTO products(name,category,purchase_price,selling_price,stock,low_stock_limit,gst_percent,created_at) VALUES(?,?,?,?,?,?,?,?)", self.values() + (datetime.now().isoformat(),)); self.clear(); self.load_products()
    def load_products(self):
        q = f"%{self.search.text().strip()}%" if hasattr(self, 'search') else "%%"
        rows = db.fetchall("SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY id DESC", (q,q))
        set_table(self.table, ["ID","Name","Category","Purchase","Selling","Stock","Low Alert","GST"], [[r['id'],r['name'],r['category'],r['purchase_price'],r['selling_price'],r['stock'],r['low_stock_limit'],r['gst_percent']] for r in rows])
    def pick_product(self, row, col):
        self.selected_id = int(self.table.item(row,0).text()); p = db.fetchone("SELECT * FROM products WHERE id=?", (self.selected_id,))
        self.name.setText(p['name']); self.category.setText(p['category'] or ''); self.purchase.setValue(p['purchase_price']); self.sell.setValue(p['selling_price']); self.stock.setValue(p['stock']); self.low.setValue(p['low_stock_limit']); self.gst.setValue(p['gst_percent'])
    def update_product(self):
        if not self.selected_id: QMessageBox.warning(self,"Select","Select product first"); return
        db.execute("UPDATE products SET name=?,category=?,purchase_price=?,selling_price=?,stock=?,low_stock_limit=?,gst_percent=? WHERE id=?", self.values() + (self.selected_id,)); self.clear(); self.load_products()
    def delete_selected(self):
        if not self.selected_id: return
        db.execute("DELETE FROM products WHERE id=?", (self.selected_id,)); self.clear(); self.load_products()
    def clear(self):
        self.selected_id = None; self.name.clear(); self.category.clear(); self.purchase.setValue(0); self.sell.setValue(0); self.stock.setValue(0); self.low.setValue(5); self.gst.setValue(0)

class CustomersPage(QWidget):
    def __init__(self): super().__init__(); self.selected_id=None; self.build_ui(); self.load()
    def build_ui(self):
        root=QVBoxLayout(self); root.addWidget(title_label("Customer Management")); form=QGridLayout(); self.name=QLineEdit(); self.phone=QLineEdit(); self.alt=QLineEdit(); self.company=QLineEdit(); self.gst=QLineEdit(); self.address=QLineEdit(); self.area=QLineEdit(); self.landmark=QLineEdit(); self.discount=QDoubleSpinBox(); self.discount.setMaximum(100); self.discount.setSuffix("%"); self.notes=QLineEdit()
        fields=[("Name",self.name),("Mobile",self.phone),("Alt Mobile",self.alt),("Company",self.company),("GST Optional",self.gst),("Delivery Address",self.address),("City/Area",self.area),("Landmark",self.landmark),("Discount",self.discount),("Notes",self.notes)]
        for i,(lab,w) in enumerate(fields): form.addWidget(QLabel(lab),i//2,i%2*2); form.addWidget(w,i//2,i%2*2+1)
        btns=QHBoxLayout(); add=QPushButton("Add Customer"); add.clicked.connect(self.add); upd=QPushButton("Update Selected"); upd.setObjectName("blue"); upd.clicked.connect(self.update); delete=QPushButton("Delete Selected"); delete.setObjectName("danger"); delete.clicked.connect(self.delete); btns.addWidget(add); btns.addWidget(upd); btns.addWidget(delete)
        self.table=QTableWidget(); self.table.cellClicked.connect(self.pick); root.addLayout(form); root.addLayout(btns); root.addWidget(self.table)
    def values(self): return (self.name.text(),self.phone.text(),self.alt.text(),self.company.text(),self.gst.text(),self.address.text(),self.area.text(),self.landmark.text(),self.notes.text(),self.discount.value())
    def add(self): db.execute("INSERT INTO customers(name,phone,alt_phone,company_name,gst_number,address,city_area,landmark,notes,discount_percent) VALUES(?,?,?,?,?,?,?,?,?,?)", self.values()); self.clear(); self.load()
    def update(self):
        if not self.selected_id: return
        db.execute("UPDATE customers SET name=?,phone=?,alt_phone=?,company_name=?,gst_number=?,address=?,city_area=?,landmark=?,notes=?,discount_percent=? WHERE id=?", self.values()+(self.selected_id,)); self.clear(); self.load()
    def delete(self):
        if self.selected_id: db.execute("DELETE FROM customers WHERE id=?",(self.selected_id,)); self.clear(); self.load()
    def load(self):
        rows=db.fetchall("SELECT * FROM customers ORDER BY id DESC")
        set_table(self.table,["ID","Name","Phone","Alt","Company","GST","Address","Area","Landmark","Discount%"],[[r['id'],r['name'],r['phone'],r['alt_phone'],r['company_name'],r['gst_number'],r['address'],r['city_area'],r['landmark'],r['discount_percent']] for r in rows])
    def pick(self,row,col):
        self.selected_id=int(self.table.item(row,0).text()); r=db.fetchone("SELECT * FROM customers WHERE id=?",(self.selected_id,))
        self.name.setText(r['name'] or ''); self.phone.setText(r['phone'] or ''); self.alt.setText(r['alt_phone'] or ''); self.company.setText(r['company_name'] or ''); self.gst.setText(r['gst_number'] or ''); self.address.setText(r['address'] or ''); self.area.setText(r['city_area'] or ''); self.landmark.setText(r['landmark'] or ''); self.notes.setText(r['notes'] or ''); self.discount.setValue(r['discount_percent'] or 0)
    def clear(self):
        self.selected_id=None
        for w in [self.name,self.phone,self.alt,self.company,self.gst,self.address,self.area,self.landmark,self.notes]: w.clear()
        self.discount.setValue(0)

class SuppliersPage(QWidget):
    def __init__(self): super().__init__(); self.selected_id=None; self.build_ui(); self.load()
    def build_ui(self):
        root=QVBoxLayout(self); root.addWidget(title_label("Supplier / Seller Management")); form=QGridLayout(); self.name=QLineEdit(); self.phone=QLineEdit(); self.gst=QLineEdit(); self.address=QLineEdit(); self.notes=QLineEdit()
        for i,(lab,w) in enumerate([("Supplier Name",self.name),("Phone",self.phone),("GST Optional",self.gst),("Address",self.address),("Notes",self.notes)]): form.addWidget(QLabel(lab),i,0); form.addWidget(w,i,1)
        btns=QHBoxLayout(); add=QPushButton("Add Supplier"); add.clicked.connect(self.add); upd=QPushButton("Update Selected"); upd.setObjectName("blue"); upd.clicked.connect(self.update); delete=QPushButton("Delete Selected"); delete.setObjectName("danger"); delete.clicked.connect(self.delete); btns.addWidget(add); btns.addWidget(upd); btns.addWidget(delete)
        self.table=QTableWidget(); self.table.cellClicked.connect(self.pick); root.addLayout(form); root.addLayout(btns); root.addWidget(self.table)
    def values(self): return (self.name.text(),self.phone.text(),self.address.text(),self.gst.text(),self.notes.text())
    def add(self): db.execute("INSERT INTO suppliers(name,phone,address,gst_number,notes) VALUES(?,?,?,?,?)", self.values()); self.clear(); self.load()
    def update(self):
        if self.selected_id: db.execute("UPDATE suppliers SET name=?,phone=?,address=?,gst_number=?,notes=? WHERE id=?", self.values()+(self.selected_id,)); self.clear(); self.load()
    def delete(self):
        if self.selected_id: db.execute("DELETE FROM suppliers WHERE id=?",(self.selected_id,)); self.clear(); self.load()
    def load(self):
        rows=db.fetchall("SELECT * FROM suppliers ORDER BY id DESC")
        set_table(self.table,["ID","Name","Phone","Address","GST","Notes"],[[r['id'],r['name'],r['phone'],r['address'],r['gst_number'],r['notes']] for r in rows])
    def pick(self,row,col):
        self.selected_id=int(self.table.item(row,0).text()); r=db.fetchone("SELECT * FROM suppliers WHERE id=?",(self.selected_id,)); self.name.setText(r['name'] or ''); self.phone.setText(r['phone'] or ''); self.address.setText(r['address'] or ''); self.gst.setText(r['gst_number'] or ''); self.notes.setText(r['notes'] or '')
    def clear(self): self.selected_id=None; self.name.clear(); self.phone.clear(); self.gst.clear(); self.address.clear(); self.notes.clear()

class BillingPage(QWidget):
    def __init__(self): super().__init__(); self.cart=[]; self.build_ui(); self.load_data()
    def build_ui(self):
        root=QVBoxLayout(self); root.addWidget(title_label("Billing / POS")); top=QGridLayout(); self.customer_box=QComboBox(); self.customer_box.currentIndexChanged.connect(self.customer_changed); self.customer_name=QLineEdit(); self.company=QLineEdit(); self.product_box=QComboBox(); self.qty=QSpinBox(); self.qty.setMinimum(1); self.qty.setMaximum(9999); self.item_disc=QDoubleSpinBox(); self.item_disc.setMaximum(100); self.item_disc.setSuffix("%"); self.bill_disc_percent=QDoubleSpinBox(); self.bill_disc_percent.setMaximum(100); self.bill_disc_percent.setSuffix("%"); self.bill_disc_amount=QDoubleSpinBox(); self.bill_disc_amount.setMaximum(999999); self.bill_disc_amount.setPrefix("₹"); self.payment=QComboBox(); self.payment.addItems(["Cash","UPI","Card"])
        items=[("Saved Customer",self.customer_box),("Customer Name",self.customer_name),("Company",self.company),("Product",self.product_box),("Qty",self.qty),("Item Discount",self.item_disc),("Bill Discount %",self.bill_disc_percent),("Bill Discount ₹",self.bill_disc_amount),("Payment",self.payment)]
        for i,(lab,w) in enumerate(items): top.addWidget(QLabel(lab),i//3,i%3*2); top.addWidget(w,i//3,i%3*2+1)
        btns=QHBoxLayout(); add=QPushButton("Add to Bill"); add.clicked.connect(self.add_to_cart); save=QPushButton("Save Bill + PDF"); save.clicked.connect(self.save_bill); clear=QPushButton("Clear Cart"); clear.setObjectName("danger"); clear.clicked.connect(self.clear_cart); btns.addWidget(add); btns.addWidget(save); btns.addWidget(clear)
        self.table=QTableWidget(); self.total_label=title_label("Grand Total: ₹0.00",18); self.total_label.setStyleSheet("color:#22C55E;"); root.addLayout(top); root.addLayout(btns); root.addWidget(self.table); root.addWidget(self.total_label)
    def load_data(self):
        self.product_box.clear(); self.customer_box.clear(); self.customer_box.addItem("Walk-in / No saved customer", None)
        for c in db.fetchall("SELECT * FROM customers ORDER BY name"): self.customer_box.addItem(f"{c['name']} | {c['phone']} | Disc {c['discount_percent'] or 0}%", c['id'])
        for r in db.fetchall("SELECT * FROM products WHERE stock>0 ORDER BY name"): self.product_box.addItem(f"{r['name']} | Stock:{r['stock']} | ₹{r['selling_price']}", r['id'])
    def customer_changed(self):
        cid=self.customer_box.currentData()
        if cid:
            c=db.fetchone("SELECT * FROM customers WHERE id=?",(cid,)); self.customer_name.setText(c['name'] or ''); self.company.setText(c['company_name'] or ''); self.bill_disc_percent.setValue(c['discount_percent'] or 0)
    def add_to_cart(self):
        pid=self.product_box.currentData()
        if not pid: QMessageBox.warning(self,"No Product","Add product in inventory first."); return
        p=db.fetchone("SELECT * FROM products WHERE id=?",(pid,)); qty=self.qty.value()
        if qty>p['stock']: QMessageBox.warning(self,"Stock Error","Not enough stock"); return
        price=p['selling_price']; disc=self.item_disc.value(); base=price*qty; base_after=base-(base*disc/100); settings=db.fetchone("SELECT * FROM shop_settings WHERE id=1"); gst=base_after*p['gst_percent']/100 if settings['gst_enabled'] else 0; total=base_after+gst; profit=(price-p['purchase_price'])*qty - (base*disc/100)
        self.cart.append({'pid':pid,'name':p['name'],'qty':qty,'purchase_price':p['purchase_price'],'price':price,'gst':p['gst_percent'],'disc':disc,'total':total,'profit':profit}); self.refresh_cart()
    def refresh_cart(self):
        set_table(self.table,["Product ID","Name","Qty","Price","Item Disc%","GST%","Total","Profit"],[[i['pid'],i['name'],i['qty'],i['price'],i['disc'],i['gst'],f"{i['total']:.2f}",f"{i['profit']:.2f}"] for i in self.cart]); subtotal=sum(i['total'] for i in self.cart); grand=subtotal-(subtotal*self.bill_disc_percent.value()/100)-self.bill_disc_amount.value(); self.total_label.setText(f"Grand Total: ₹{grand:.2f}")
    def clear_cart(self): self.cart=[]; self.refresh_cart()
    def save_bill(self):
        if not self.cart: QMessageBox.warning(self,"Empty","Cart is empty"); return
        bill_no=datetime.now().strftime("BILL%Y%m%d%H%M%S"); today=date.today().strftime("%Y-%m-%d"); subtotal=sum(i['price']*i['qty'] for i in self.cart); gst_amount=sum(i['total']-(i['price']*i['qty']-(i['price']*i['qty']*i['disc']/100)) for i in self.cart); cart_total=sum(i['total'] for i in self.cart); discount=cart_total*self.bill_disc_percent.value()/100+self.bill_disc_amount.value(); grand=cart_total-discount; gross_profit=sum(i['profit'] for i in self.cart)-discount
        cur=db.execute("INSERT INTO sales(bill_no,date,customer_id,customer_name,company_name,subtotal,gst_amount,discount,discount_percent,grand_total,payment_mode,gross_profit) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(bill_no,today,self.customer_box.currentData(),self.customer_name.text(),self.company.text(),subtotal,gst_amount,discount,self.bill_disc_percent.value(),grand,self.payment.currentText(),gross_profit)); sale_id=cur.lastrowid
        for i in self.cart:
            db.execute("INSERT INTO sale_items(sale_id,product_id,product_name,qty,purchase_price,price,gst_percent,discount_percent,total,profit) VALUES(?,?,?,?,?,?,?,?,?,?)",(sale_id,i['pid'],i['name'],i['qty'],i['purchase_price'],i['price'],i['gst'],i['disc'],i['total'],i['profit'])); db.execute("UPDATE products SET stock=stock-? WHERE id=?",(i['qty'],i['pid']))
        self.create_pdf(bill_no,sale_id); QMessageBox.information(self,"Success",f"Bill saved: {bill_no}"); self.clear_cart(); self.load_data()
    def create_pdf(self,bill_no,sale_id):
        if canvas is None: return
        Path("bills").mkdir(exist_ok=True); s=db.fetchone("SELECT * FROM shop_settings WHERE id=1"); sale=db.fetchone("SELECT * FROM sales WHERE id=?",(sale_id,)); items=db.fetchall("SELECT * FROM sale_items WHERE sale_id=?",(sale_id,)); c=canvas.Canvas(f"bills/{bill_no}.pdf",pagesize=A4); w,h=A4; y=h-50; c.setFont("Helvetica-Bold",18); c.drawString(50,y,s['shop_name'] or APP_NAME); y-=20; c.setFont("Helvetica",10)
        for line in [f"Business: {s['business_name'] or ''}",f"Address: {s['address'] or ''}",f"Phone: {s['phone'] or ''}"]: c.drawString(50,y,line); y-=15
        if s['gst_enabled'] and s['gst_number']: c.drawString(50,y,f"GST No: {s['gst_number']}"); y-=15
        y-=15; c.drawString(50,y,f"Bill No: {bill_no}   Date: {sale['date']}"); y-=15; c.drawString(50,y,f"Customer: {sale['customer_name'] or '-'}   Company: {sale['company_name'] or '-'}"); y-=30
        for it in items:
            c.drawString(50,y,f"{it['product_name'][:22]}  Qty:{it['qty']}  Rate:{it['price']:.2f}  Total:{it['total']:.2f}"); y-=15
        y-=20; c.setFont("Helvetica-Bold",12); c.drawString(390,y,f"Grand Total: ₹{sale['grand_total']:.2f}"); c.save()

class PurchasePage(QWidget):
    def __init__(self): super().__init__(); self.items=[]; self.build_ui(); self.load_data()
    def build_ui(self):
        root=QVBoxLayout(self); root.addWidget(title_label("Purchase Entry")); top=QGridLayout(); self.supplier_box=QComboBox(); self.product_box=QComboBox(); self.qty=QSpinBox(); self.qty.setMinimum(1); self.qty.setMaximum(999999); self.price=QDoubleSpinBox(); self.price.setMaximum(999999); self.price.setPrefix("₹"); self.gst=QDoubleSpinBox(); self.gst.setMaximum(100); self.gst.setSuffix("%"); self.other=QDoubleSpinBox(); self.other.setMaximum(999999); self.other.setPrefix("₹"); self.payment=QComboBox(); self.payment.addItems(["Cash","UPI","Card","Credit"]); self.notes=QLineEdit()
        for i,(lab,w) in enumerate([("Supplier/Seller",self.supplier_box),("Product",self.product_box),("Qty",self.qty),("Purchase Price",self.price),("GST %",self.gst),("Other Charges",self.other),("Payment",self.payment),("Notes",self.notes)]): top.addWidget(QLabel(lab),i//2,i%2*2); top.addWidget(w,i//2,i%2*2+1)
        btns=QHBoxLayout(); add=QPushButton("Add Item"); add.clicked.connect(self.add_item); save=QPushButton("Save Purchase + Stock Increase"); save.clicked.connect(self.save_purchase); clear=QPushButton("Clear"); clear.setObjectName("danger"); clear.clicked.connect(self.clear); btns.addWidget(add); btns.addWidget(save); btns.addWidget(clear)
        self.table=QTableWidget(); self.total=title_label("Purchase Total: ₹0.00",18); self.total.setStyleSheet("color:#22C55E;"); root.addLayout(top); root.addLayout(btns); root.addWidget(self.table); root.addWidget(self.total)
    def load_data(self):
        self.supplier_box.clear(); self.product_box.clear()
        for s in db.fetchall("SELECT * FROM suppliers ORDER BY name"): self.supplier_box.addItem(f"{s['name']} | {s['phone']}",s['id'])
        for p in db.fetchall("SELECT * FROM products ORDER BY name"): self.product_box.addItem(f"{p['name']} | Current Stock:{p['stock']}",p['id'])
    def add_item(self):
        pid=self.product_box.currentData()
        if not pid: QMessageBox.warning(self,"No Product","Add product in inventory first."); return
        p=db.fetchone("SELECT * FROM products WHERE id=?",(pid,)); qty=self.qty.value(); price=self.price.value(); gst_amt=qty*price*self.gst.value()/100; total=qty*price+gst_amt; self.items.append({'pid':pid,'name':p['name'],'qty':qty,'price':price,'gst':self.gst.value(),'total':total}); self.refresh()
    def refresh(self): set_table(self.table,["Product ID","Name","Qty","Purchase Price","GST%","Total"],[[i['pid'],i['name'],i['qty'],i['price'],i['gst'],f"{i['total']:.2f}"] for i in self.items]); self.total.setText(f"Purchase Total: ₹{sum(i['total'] for i in self.items)+self.other.value():.2f}")
    def clear(self): self.items=[]; self.refresh()
    def save_purchase(self):
        if not self.items: QMessageBox.warning(self,"Empty","No purchase item added"); return
        pur_no=datetime.now().strftime("PUR%Y%m%d%H%M%S"); today=date.today().strftime("%Y-%m-%d"); supplier_id=self.supplier_box.currentData(); sup=db.fetchone("SELECT * FROM suppliers WHERE id=?",(supplier_id,)) if supplier_id else None; subtotal=sum(i['qty']*i['price'] for i in self.items); gst_amount=sum(i['total']-i['qty']*i['price'] for i in self.items); grand=sum(i['total'] for i in self.items)+self.other.value()
        cur=db.execute("INSERT INTO purchases(purchase_no,date,supplier_id,supplier_name,subtotal,gst_amount,other_charges,grand_total,payment_mode,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(pur_no,today,supplier_id,sup['name'] if sup else '',subtotal,gst_amount,self.other.value(),grand,self.payment.currentText(),self.notes.text())); purchase_id=cur.lastrowid
        for i in self.items: db.execute("INSERT INTO purchase_items(purchase_id,product_id,product_name,qty,purchase_price,gst_percent,total) VALUES(?,?,?,?,?,?,?)",(purchase_id,i['pid'],i['name'],i['qty'],i['price'],i['gst'],i['total'])); db.execute("UPDATE products SET stock=stock+?, purchase_price=? WHERE id=?",(i['qty'],i['price'],i['pid']))
        QMessageBox.information(self,"Saved",f"Purchase saved: {pur_no}\nStock increased automatically."); self.clear(); self.load_data()

class PurchaseHistoryPage(QWidget):
    def __init__(self): super().__init__(); root=QVBoxLayout(self); root.addWidget(title_label("Purchase History")); btn=QPushButton("Refresh"); btn.clicked.connect(self.load); self.table=QTableWidget(); root.addWidget(btn); root.addWidget(self.table); self.load()
    def load(self): rows=db.fetchall("SELECT purchase_no,date,supplier_name,subtotal,gst_amount,other_charges,grand_total,payment_mode FROM purchases ORDER BY id DESC"); set_table(self.table,["Purchase No","Date","Supplier","Subtotal","GST","Other","Grand Total","Payment"],[[r['purchase_no'],r['date'],r['supplier_name'],r['subtotal'],r['gst_amount'],r['other_charges'],r['grand_total'],r['payment_mode']] for r in rows])

class ExpensePage(QWidget):
    def __init__(self): super().__init__(); self.build_ui(); self.load_expenses()
    def build_ui(self):
        root=QVBoxLayout(self); root.addWidget(title_label("Expense Management")); form=QGridLayout(); self.amount=QDoubleSpinBox(); self.amount.setMaximum(999999); self.amount.setPrefix("₹"); self.category=QLineEdit(); self.desc=QLineEdit(); form.addWidget(QLabel("Amount"),0,0); form.addWidget(self.amount,0,1); form.addWidget(QLabel("Category"),0,2); form.addWidget(self.category,0,3); form.addWidget(QLabel("Description"),1,0); form.addWidget(self.desc,1,1,1,3); btn=QPushButton("Add Expense"); btn.clicked.connect(self.add_expense); self.table=QTableWidget(); root.addLayout(form); root.addWidget(btn); root.addWidget(self.table)
    def add_expense(self): db.execute("INSERT INTO expenses(date,amount,category,description) VALUES(?,?,?,?)",(date.today().strftime("%Y-%m-%d"),self.amount.value(),self.category.text(),self.desc.text())); self.amount.setValue(0); self.category.clear(); self.desc.clear(); self.load_expenses()
    def load_expenses(self): rows=db.fetchall("SELECT * FROM expenses ORDER BY id DESC"); set_table(self.table,["Date","Amount","Category","Description"],[[r['date'],r['amount'],r['category'],r['description']] for r in rows])

class SalesHistoryPage(QWidget):
    def __init__(self): super().__init__(); root=QVBoxLayout(self); root.addWidget(title_label("Sales History")); btn=QPushButton("Refresh"); btn.clicked.connect(self.load); self.table=QTableWidget(); root.addWidget(btn); root.addWidget(self.table); self.load()
    def load(self): rows=db.fetchall("SELECT bill_no,date,customer_name,company_name,grand_total,payment_mode,gross_profit FROM sales ORDER BY id DESC"); set_table(self.table,["Bill No","Date","Customer","Company","Total","Payment","Gross Profit"],[[r['bill_no'],r['date'],r['customer_name'],r['company_name'],r['grand_total'],r['payment_mode'],r['gross_profit']] for r in rows])

class ReportsPage(QWidget):
    def __init__(self): super().__init__(); self.build_ui()
    def build_ui(self): root=QVBoxLayout(self); root.addWidget(title_label("Reports & Analytics")); btn=QPushButton("Refresh Reports"); btn.clicked.connect(self.refresh); self.text=QTextEdit(); self.text.setReadOnly(True); root.addWidget(btn); root.addWidget(self.text); self.refresh()
    def refresh(self):
        today=date.today().strftime("%Y-%m-%d"); month=date.today().strftime("%Y-%m"); year=date.today().strftime("%Y")
        def val(q,p=()): return db.fetchone(q,p)['v']
        ts=val("SELECT COALESCE(SUM(grand_total),0) v FROM sales WHERE date=?",(today,)); ms=val("SELECT COALESCE(SUM(grand_total),0) v FROM sales WHERE substr(date,1,7)=?",(month,)); ys=val("SELECT COALESCE(SUM(grand_total),0) v FROM sales WHERE substr(date,1,4)=?",(year,)); tp=val("SELECT COALESCE(SUM(grand_total),0) v FROM purchases WHERE date=?",(today,)); mp=val("SELECT COALESCE(SUM(grand_total),0) v FROM purchases WHERE substr(date,1,7)=?",(month,)); yp=val("SELECT COALESCE(SUM(grand_total),0) v FROM purchases WHERE substr(date,1,4)=?",(year,)); te=val("SELECT COALESCE(SUM(amount),0) v FROM expenses WHERE date=?",(today,)); me=val("SELECT COALESCE(SUM(amount),0) v FROM expenses WHERE substr(date,1,7)=?",(month,)); ye=val("SELECT COALESCE(SUM(amount),0) v FROM expenses WHERE substr(date,1,4)=?",(year,)); tg=val("SELECT COALESCE(SUM(gross_profit),0) v FROM sales WHERE date=?",(today,)); mg=val("SELECT COALESCE(SUM(gross_profit),0) v FROM sales WHERE substr(date,1,7)=?",(month,)); yg=val("SELECT COALESCE(SUM(gross_profit),0) v FROM sales WHERE substr(date,1,4)=?",(year,))
        self.text.setText(f"TODAY\nSales: {money(ts)}\nPurchase: {money(tp)}\nExpenses: {money(te)}\nNet Profit/Loss: {money(tg-te)}\n\nMONTHLY\nSales: {money(ms)}\nPurchase: {money(mp)}\nExpenses: {money(me)}\nNet Profit/Loss: {money(mg-me)}\n\nYEARLY\nSales: {money(ys)}\nPurchase: {money(yp)}\nExpenses: {money(ye)}\nNet Profit/Loss: {money(yg-ye)}")

class SettingsPage(QWidget):
    def __init__(self): super().__init__(); self.build_ui(); self.load_settings()
    def build_ui(self):
        root=QVBoxLayout(self); root.addWidget(title_label("Shop Settings & Backup")); form=QGridLayout(); self.shop=QLineEdit(); self.business=QLineEdit(); self.gst_no=QLineEdit(); self.phone=QLineEdit(); self.logo=QLineEdit(); self.address=QTextEdit(); self.gst_enabled=QCheckBox("Enable GST Invoice"); save=QPushButton("Save Settings"); save.clicked.connect(self.save_settings); bkup=QPushButton("Backup Database"); bkup.clicked.connect(self.backup); restore=QPushButton("Restore Database"); restore.setObjectName("danger"); restore.clicked.connect(self.restore)
        for i,(lab,w) in enumerate([("Shop Name",self.shop),("Business Name",self.business),("GST Number",self.gst_no),("Phone",self.phone),("Logo Path",self.logo)]): form.addWidget(QLabel(lab),i,0); form.addWidget(w,i,1)
        form.addWidget(QLabel("Address"),5,0); form.addWidget(self.address,5,1); form.addWidget(self.gst_enabled,6,1); root.addLayout(form); root.addWidget(save); root.addWidget(bkup); root.addWidget(restore); root.addStretch()
    def load_settings(self):
        s=db.fetchone("SELECT * FROM shop_settings WHERE id=1"); self.shop.setText(s['shop_name'] or ''); self.business.setText(s['business_name'] or ''); self.gst_no.setText(s['gst_number'] or ''); self.phone.setText(s['phone'] or ''); self.logo.setText(s['logo_path'] or ''); self.address.setText(s['address'] or ''); self.gst_enabled.setChecked(bool(s['gst_enabled']))
    def save_settings(self): db.execute("UPDATE shop_settings SET shop_name=?,business_name=?,gst_number=?,address=?,phone=?,logo_path=?,gst_enabled=? WHERE id=1",(self.shop.text(),self.business.text(),self.gst_no.text(),self.address.toPlainText(),self.phone.text(),self.logo.text(),1 if self.gst_enabled.isChecked() else 0)); QMessageBox.information(self,"Saved","Settings updated")
    def backup(self):
        f,_=QFileDialog.getSaveFileName(self,"Save Backup","your_dukaan_manager_backup.db","Database (*.db)")
        if f: shutil.copy(DB_FILE,f); QMessageBox.information(self,"Backup","Backup saved")
    def restore(self):
        f,_=QFileDialog.getOpenFileName(self,"Restore Backup","","Database (*.db)")
        if f: shutil.copy(f,DB_FILE); QMessageBox.information(self,"Restore","Database restored. Restart app.")

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        if Path(ICON_FILE).exists(): self.setWindowIcon(QIcon(ICON_FILE))
        self.resize(1320,790); self.setStyleSheet(STYLE); self.stack=QStackedWidget(); self.login_page=LoginPage(self); self.stack.addWidget(self.login_page); self.setCentralWidget(self.stack)
    def show_main_app(self):
        main=QWidget(); root=QHBoxLayout(main); root.setContentsMargins(0,0,0,0); sidebar=QFrame(); sidebar.setFixedWidth(255); sidebar.setStyleSheet("background:#020617;"); side=QVBoxLayout(sidebar); brand=QLabel("Your Dukaan\nManager"); brand.setFont(QFont("Segoe UI",18,QFont.Bold)); brand.setAlignment(Qt.AlignCenter); brand.setStyleSheet("padding:20px;color:#22C55E;"); side.addWidget(brand)
        self.pages=QStackedWidget(); self.dashboard=DashboardPage(); self.billing=BillingPage(); self.purchase=PurchasePage(); self.inventory=InventoryPage(); self.customers=CustomersPage(); self.suppliers=SuppliersPage(); self.expenses=ExpensePage(); self.sales=SalesHistoryPage(); self.pur_history=PurchaseHistoryPage(); self.reports=ReportsPage(); self.settings=SettingsPage()
        for p in [self.dashboard,self.billing,self.purchase,self.inventory,self.customers,self.suppliers,self.expenses,self.sales,self.pur_history,self.reports,self.settings]: self.pages.addWidget(p)
        buttons=[("Dashboard","dashboard.png",0),("Billing POS","billing.png",1),("Purchase Entry","suppliers.png",2),("Inventory","inventory.png",3),("Customers","customers.png",4),("Suppliers","suppliers.png",5),("Expenses","expenses.png",6),("Sales History","reports.png",7),("Purchase History","billing.png",8),("Reports","reports.png",9),("Settings","settings.png",10)]
        for text,icon,idx in buttons:
            b=QPushButton(text); b.setObjectName("side"); b.setIcon(asset_icon(icon)); b.setIconSize(QSize(22,22)); b.clicked.connect(lambda checked=False,i=idx:self.change_page(i)); side.addWidget(b)
        side.addStretch(); root.addWidget(sidebar); root.addWidget(self.pages); self.stack.addWidget(main); self.stack.setCurrentWidget(main); self.check_alerts()
    def change_page(self,index):
        if index==0: self.dashboard.refresh()
        if index==1: self.billing.load_data()
        if index==2: self.purchase.load_data()
        if index==3: self.inventory.load_products()
        if index==4: self.customers.load()
        if index==5: self.suppliers.load()
        if index==6: self.expenses.load_expenses()
        if index==7: self.sales.load()
        if index==8: self.pur_history.load()
        if index==9: self.reports.refresh()
        if index==10: self.settings.load_settings()
        self.pages.setCurrentIndex(index)
    def check_alerts(self):
        rows=db.fetchall("SELECT name,stock,low_stock_limit FROM products WHERE stock<=low_stock_limit")
        if rows:
            msg="\n".join([f"{r['name']} - Stock {r['stock']}" for r in rows[:10]])
            QMessageBox.warning(self,"Stock Alert",f"Low/Out of stock products:\n{msg}")

if __name__ == "__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion"); win=MainApp(); win.show(); sys.exit(app.exec())
