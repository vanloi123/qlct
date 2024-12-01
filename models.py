from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    expenses = db.relationship('Expense', backref='category', lazy=True)

def get_category_expenses():
    results = db.session.query(
        Category.name, db.func.sum(Expense.amount).label('total_amount')
    ).join(Expense).group_by(Category.name).all()
    return results
