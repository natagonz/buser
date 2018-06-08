# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy 
from config import database, secret
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import LoginManager , UserMixin, login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
from flask_mail import Mail,Message 
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField ,TextAreaField, IntegerField, DateField, SelectField, SubmitField,FloatField,DecimalField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired, EqualTo, Email, Length





app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] = database
app.config["SECRET_KEY"] = secret 
db = SQLAlchemy(app)
app.debug = True 





class User(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(200))
	email = db.Column(db.String(200))
	phone = db.Column(db.String(200))
	password = db.Column(db.String(500))
	role = db.Column(db.String(200))

	def is_active(self):
		return True

	def get_id(self):
		return self.id

	def is_authenticated(self):
		return self.authenticated

	def is_anonymous(self):
		return False


class Location(db.Model):
	id = db.Column(db.Integer,primary_key=True) 
	name = db.Column(db.String(200))
	def __repr__(self):
		return '{}'.format(self.name)


class Route(db.Model):
	id = db.Column(db.Integer,primary_key=True) 
	pickup = db.Column(db.String(200))
	drop = db.Column(db.String(200))
	price = db.Column(db.BigInteger())


class Book(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	email = db.Column(db.String(200))
	username = db.Column(db.String(200))
	phone = db.Column(db.String(200))	
	date = db.Column(db.DateTime())	
	detail = db.Column(db.Text())
	pickup = db.Column(db.String(200))
	drop = db.Column(db.String(200))
	price = db.Column(db.BigInteger())
	

def location_query():
	return Location.query.all()	

#################################################### Decorator ##############################################################################

#login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "UserLogin"

#user loader
@login_manager.user_loader
def user_loader(user_id):
	return User.query.get(int(user_id))

#fungsi mail
app.config.from_pyfile("config.py") 
mail = Mail(app)
s = URLSafeTimedSerializer("secret")



##################################################### form #######################################
class AdminRegisterForm(FlaskForm):
	username = StringField("username",validators=[Length(max=100),InputRequired()])
	email = StringField("email",validators=[Email(),Length(max=100)])
	password = PasswordField("password",validators=[InputRequired(),Length(max=100)])

class AdminLoginForm(FlaskForm):
	email = StringField("email",validators=[Email(),Length(max=100)])
	password = PasswordField("password",validators=[InputRequired(),Length(max=100)])



class UserRegisterForm(FlaskForm):
	username = StringField("username",validators=[Length(max=100),InputRequired()])
	email = StringField("email",validators=[Email(),Length(max=100)])
	phone = StringField("phone",validators=[Length(max=100)])


class LoginForm(FlaskForm):
	email = StringField("Email",validators=[Email(),Length(max=100)])
	password = PasswordField("Password",validators=[InputRequired()])


class AddLocationForm(FlaskForm):
	name = StringField("Name",validators=[InputRequired(),Length(max=100)])


class AddRouteForm(FlaskForm):
	pickup = StringField("Pickup")
	drop = QuerySelectField("Drop",query_factory=location_query)
	price = IntegerField("Harga",validators=[InputRequired()])


class BookForm(FlaskForm):
	pickup = QuerySelectField(query_factory=location_query)
	drop = QuerySelectField(query_factory=location_query)


class ConfirmBookForm(FlaskForm):
	username = StringField("username",validators=[Length(max=100),InputRequired()])
	email = StringField("email",validators=[Email(),Length(max=100)])
	phone = StringField("phone",validators=[Length(max=100)])	
	date = DateField("date",format="%m/%d/%Y")
	detail = TextAreaField("notes")





@app.route("/",methods=["GET","POST"])
def Index():
	form = BookForm()
	if form.validate_on_submit():
		pickup = str(form.pickup.data) 
		drop = str(form.drop.data)
		route = Route.query.filter_by(pickup=pickup,drop=drop).first()
		if route :
			return redirect(url_for("BookConfirm",pickup=pickup,drop=drop)) 
		else :
			return redirect(url_for("NoRoute",pickup=pickup,drop=drop))			
		
	return render_template("index.html",form=form)




@app.route("/noroute/<pickup>/<drop>",methods=["GET","POST"])
def NoRoute(pickup,drop):
	return render_template("noroute.html",pickup=pickup,drop=drop)	




@app.route("/book/<pickup>/<drop>",methods=["GET","POST"])
def BookConfirm(pickup,drop):
	form = ConfirmBookForm()
	route = Route.query.filter_by(pickup=pickup,drop=drop).first()
	price = route.price
	if form.validate_on_submit():
		book = Book(username=form.username.data,email=form.email.data,phone=form.phone.data,pickup=pickup,drop=drop,price=price,date=form.date.data,detail=form.detail.data)
		db.session.add(book)
		db.session.commit()	

		return redirect(url_for("Payment",id=book.id))
	return render_template("bookconfirm.html",pickup=pickup,drop=drop,form=form,price=price)
	

@app.route("/payment/<id>",methods=["GET","POST"])
def Payment(id):
	book = Book.query.filter_by(id=id).first()
	return render_template("payment.html",book=book)














@app.route("/admin/register",methods=["GET","POST"])
def AdminRegister():
	form = AdminRegisterForm()
	if form.validate_on_submit():
		hass = generate_password_hash(form.password.data,method="sha256")
		admin = User(username=form.username.data,email=form.email.data,password=hass,role="admin")

		db.session.add(admin)
		db.session.commit()

		login_user(admin)
		return redirect(url_for("AdminDashboard"))
	return render_template("auth/admin_register.html",form=form)	

@app.route("/admin/login",methods=["GET","POST"])
def AdminLogin():
	form = AdminLoginForm()
	if form.validate_on_submit():
		admin = User.query.filter_by(email=form.email.data).first()
		if admin:
			if check_password_hash(admin.password,form.password.data):
				login_user(admin)

				flash("Login Berhasil","success")
				return redirect(url_for("AdminDashboard"))
		flash("Invalid Login","danger")
	return render_template("auth/admin_login.html",form=form)	
				

@app.route("/admin/dashboard",methods=["GET","POST"])
@login_required
def AdminDashboard():
	return render_template("dashboard/dashboard.html")



@app.route("/dashboard/admin/charter",methods=["GET","POST"])
def AddLocation():
	locations = Location.query.all()
	form = AddLocationForm()		
	if form.validate_on_submit():
		name = form.name.data.lower()
		check_location = Location.query.filter_by(name=name).first()
		if check_location :
			flash("Lokasi tidak boleh sama","danger")
		else :	
			location = Location(name=name)
			db.session.add(location)
			db.session.commit()
			return redirect(url_for("AddLocation"))
	return render_template("dashboard/location.html",form=form,locations=locations)


@app.route("/dashboard/admin/route/<location_name>",methods=["GET","POST"])
@login_required
def AddRoute(location_name):
	route = Route.query.filter_by(pickup=location_name).all()
	form = AddRouteForm()
	form.pickup.data = location_name	
	if form.validate_on_submit():
		drop = str(form.drop.data)
		check = Route.query.filter_by(pickup=location_name,drop=drop).first() 						
		if location_name == drop :
			flash("Lokasi tidak boleh sama","danger")			
		elif check:
			flash("Rute sudah ada","danger")				
		else :		
			route = Route(pickup=location_name,drop=form.drop.data,price=form.price.data)
			db.session.add(route)
			db.session.commit()
			return redirect(url_for("AddRoute",location_name=location_name))
	return render_template("dashboard/route.html",route=route,form=form)














































if __name__ == "__main__":
	app.run()

