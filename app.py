from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import pandas as pd
from datetime import datetime
import io
import portalocker

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                       id INTEGER PRIMARY KEY,
                       date TEXT,
                       category TEXT,
                       amount REAL,
                       timestamp TEXT
                       )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
                       id INTEGER PRIMARY KEY,
                       name TEXT UNIQUE
                       )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
                       id INTEGER PRIMARY KEY,
                       category_id INTEGER,
                       amount REAL,
                       FOREIGN KEY (category_id) REFERENCES categories(id)
                       )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses')
    expenses = cursor.fetchall()
    # Định dạng lại ngày tháng
    expenses = [(e[0], datetime.strptime(e[1], "%Y-%m-%d").strftime("%d/%m/%Y"), e[2], int(e[3])) for e in expenses]
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    cursor.execute('''SELECT c.name, COALESCE(SUM(e.amount), 0) AS total_spent, COALESCE(b.amount, 0) AS budget
                      FROM categories c
                      LEFT JOIN expenses e ON c.name = e.category
                      LEFT JOIN budgets b ON c.id = b.category_id
                      GROUP BY c.name''')
    budget_status = cursor.fetchall()
    budget_status = [(b[0], int(b[2]), int(b[1])) for b in budget_status]  # Đảm bảo logic so sánh đúng
    conn.close()
    return render_template('index.html', expenses=expenses, categories=categories, budget_status=budget_status)

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO expenses (date, category, amount, timestamp) VALUES (?, ?, ?, ?)',
                       (date, category, amount, timestamp))
        conn.commit()
        conn.close()
        flash('Đã thêm chi tiêu thành công')
        return redirect(url_for('index'))
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return render_template('add_expense.html', categories=categories)

@app.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'POST':
        name = request.form['name']
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        flash('Đã thêm danh mục thành công')
        return redirect(url_for('manage_categories'))
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return render_template('categories.html', categories=categories)

@app.route('/edit_category/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    if request.method == 'POST':
        name = request.form['name']
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (name, id))
        conn.commit()
        conn.close()
        flash('Đã cập nhật danh mục thành công')
        return redirect(url_for('manage_categories'))
    else:
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories WHERE id = ?', (id,))
        category = cursor.fetchone()
        conn.close()
        return render_template('edit_category.html', category=category)

@app.route('/delete_category/<int:id>', methods=['POST'])
def delete_category(id):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categories WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Đã xóa danh mục thành công')
    return redirect(url_for('manage_categories'))

@app.route('/budgets', methods=['GET', 'POST'])
def manage_budgets():
    if request.method == 'POST':
        category_id = request.form['category_id']
        amount = request.form['amount']
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO budgets (category_id, amount) VALUES (?, ?)',
                       (category_id, amount))
        conn.commit()
        conn.close()
        flash('Đã thêm ngân sách thành công')
        return redirect(url_for('manage_budgets'))
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return render_template('budgets.html', categories=categories)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    if request.method == 'POST':
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE expenses SET date = ?, category = ?, amount = ? WHERE id = ?',
                       (date, category, amount, id))
        conn.commit()
        conn.close()
        flash('Đã cập nhật chi tiêu thành công')
        return redirect(url_for('index'))
    else:
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (id,))
        expense = cursor.fetchone()
        cursor.execute('SELECT * FROM categories')
        categories = cursor.fetchall()
        conn.close()
        return render_template('edit_expense.html', expense=expense, categories=categories)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Đã xóa chi tiêu thành công')
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_data():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses')
    conn.commit()
    conn.close()
    flash('Đã reset dữ liệu thành công')
    return redirect(url_for('index'))

@app.route('/export', methods=['GET'])
def export_data():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT c.name, COALESCE(SUM(e.amount), 0) AS total_spent, COALESCE(b.amount, 0) AS budget
                      FROM categories c
                      LEFT JOIN expenses e ON c.name = e.category
                      LEFT JOIN budgets b ON c.id = b.category_id
                      GROUP BY c.name''')
    budget_status = cursor.fetchall()
    conn.close()

    # Thêm cột Trạng thái vào dữ liệu
    budget_status_with_state = []
    for row in budget_status:
        category, total_spent, budget = row
        if total_spent > budget:
            state = 'Quá ngân sách'
        elif total_spent == budget:
            state = 'Đúng ngân sách'
        else:
            state = 'Dưới ngân sách'
        budget_status_with_state.append((category, total_spent, budget, state))

    df = pd.DataFrame(budget_status_with_state, columns=["Danh mục", "Tổng chi tiêu", "Ngân sách", "Trạng thái"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Trạng thái ngân sách')

    output.seek(0)
    return send_file(output, as_attachment=True, download_name="trang_thai_ngan_sach.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/reports')
def reports():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT category, SUM(amount) as total_amount
                      FROM expenses
                      GROUP BY category
                      ORDER BY category''')
    category_expenses = cursor.fetchall()
    category_expenses = [(c[0], int(c[1])) for c in category_expenses]  # Làm tròn số tiền thành số nguyên
    cursor.execute('''SELECT date, category, time(timestamp) as time, SUM(amount) as total_amount
                      FROM expenses
                      GROUP BY date, category, time
                      ORDER BY date, category, time''')
    report_data = cursor.fetchall()
    report_data  = [(datetime.strptime(r[0], "%Y-%m-%d").strftime("%d/%m/%Y"), r[1], r[2], int(r[3])) for r in report_data]  # Làm tròn số tiền
    cursor.execute('SELECT SUM(amount) FROM expenses')
    total_expense = int(cursor.fetchone()[0])  # Tổng số tiền đã chi tiêu
    conn.close()
    return render_template('reports.html', category_expenses=category_expenses, report_data=report_data, total_expense=total_expense)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
