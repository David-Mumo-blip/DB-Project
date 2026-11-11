# Hunger Hunt

A campus food-ordering site. Students order from vendors and pay from a wallet; vendors manage stock and fulfil orders; an admin approves new vendors.

## Setup (do this once)
1. `git clone <repo-url>` (already cloned? run `git checkout main`, then `git pull`)
2. `python -m venv venv`
3. Activate it: CMD `venv\Scripts\activate` | Git Bash `source venv/Scripts/activate` | Mac/Linux `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. Copy `config.example.py` to `config.py` and put YOUR MySQL password in it. `DB_NAME` must be the database you created (`Hunger`).
6. Create the database. In MySQL Workbench open `DB_Scripts/actualsql.sql` and run it. **It wipes and recreates all tables.**
   - Already have data you want to keep? Don't re-run it. Run `DB_Scripts/admin_migration.sql` (admin role) and then `DB_Scripts/migrate_to_latest.sql` (vendor balance/goal, order quantity, notifications) instead.
7. `python migrate.py` (brings an existing database up to date; `--check` only reports what is missing)
8. `python app.py`
9. Open http://127.0.0.1:5000/api/health. It should say `"connected"`. Then open http://127.0.0.1:5000/

## Test accounts (from actualsql.sql)
| Role | Email | Notes |
|---|---|---|
| Student | `student@test.com` | starts with KSh 1000 |
| Vendor | `pate@test.com`, `georgies@test.com`, `kerinton@test.com`, `upesi@test.com` | start with balance 0 |
| Admin | `admin@test.com` | approves vendor applications |

All seeded accounts share one password (whatever the hash in `actualsql.sql` was made from). If you don't know it, register fresh accounts at `/auth/role`, or generate a new hash with `python -c "from werkzeug.security import generate_password_hash as g; print(g('yourpassword'))"` and paste it into the `@pw` line before re-running the script.

## How it fits together
```
app.py              starts Flask, registers the blueprints below, injects wallet / notification counts into pages
db.py               get_db(): opens a MySQL connection from config.py
routes/auth.py      register (student or vendor, with photo upload), login, logout
routes/student.py   vendor list, vendor menu, cart, checkout (pay + reduce stock + notify vendor)
routes/vendor.py    dashboard, orders, mark ready, products (add / edit / stock / delete), revenue goal
routes/admin.py     approve or reject vendor applications
routes/notifications.py   notify() helper + the /notifications inbox
routes/uploads.py   saving uploaded images and finding image URLs
templates/          one HTML file per page
static/images/      bundled photos      static/uploads/   photos uploaded by vendors
DB_Scripts/actualsql.sql   the one source of truth for the database
```

The rules the app follows:
- **Stock** only goes down when a student *pays* (checkout). Adding to cart does not reserve anything.
- **Vendor money** only arrives when the vendor marks an order *ready*.
- **Orders** are created at payment and appear on that vendor's Orders page. Marking ready removes them from the page and notifies the student.
- Everything students see (menus, prices, stock, photos) is read from the database. Nothing is hardcoded.

## Testing it by hand
Use two browser windows (or one normal + one private) so you can be a student and a vendor at the same time.

1. **Admin approval**: register a vendor at `/auth/role` (fill in the photo and goal). Try logging in as them: "under review". Log in as `admin@test.com`, approve them, then log in as the vendor.
2. **Add a product**: vendor dashboard > **+ Add Product**. Fill in every field and upload a photo. It shows in the inventory table with a thumbnail. Add one *without* a photo: it shows "No photo yet".
3. **Edit / manage stock**: click **Edit** to change any field or replace the photo. In the stock column type a number and press **+** or **-**. Then open that vendor's page as a student: the stock and price match.
4. **Hide a product**: Edit > Availability > Hidden. The student sees "Out of Stock" and can't add it.
5. **Order**: as a student, add items to the cart (stock is unchanged), then **Pay with Wallet**. Check: wallet dropped by the total, stock dropped, the vendor has a 🔔 notification and a new row on **Orders**.
6. **Out of stock race**: set a product's stock to 2. Put 1 in each of three students' carts (three accounts), then pay one after another. The first two succeed, the third gets "out of stock" and keeps their money.
7. **Ready**: as the vendor, **Mark Ready**. The order disappears, the student gets a notification, the vendor balance and goal progress bar go up.
8. **Own order**: vendor Orders page > "Order your own product". No payment, the stock drops, and it appears with "You (own order)". Marking it ready adds no money.

## Every day (git)
1. Activate the venv
2. `git checkout main`, then `git pull`
3. Switch to your branch: `git checkout (your-branch)`, then `git merge main`
4. Work, commit small and often
5. `git push`, then open a pull request. A teammate reviews before it merges into main

## Rules
- Never commit `config.py` (it has your own password)
- Only Leon and I edit `app.py` and `routes/`
- Tell the group chat before changing the SQL scripts
