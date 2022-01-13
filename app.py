from flask import Flask, render_template ,request, flash , redirect , url_for , session, logging
#from data import articles
import mysql.connector
from  wtforms import Form , StringField, TextAreaField,PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
#arrticles = articles()

cnx = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="1234Farid1234",
    database= 'webflaskapp')
# dictionary true mean this will give you row in dictionary 
#check this link for further 
#https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursordict.html
cur = cnx.cursor()


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Article list route
@app.route('/articles')
def articles():
    cur = cnx.cursor(buffered=True,dictionary=True)

    # Get Articles
    cur.execute('SELECT * FROM articles')
    articles = cur.fetchall()
       
    if articles is not None:

        if len(articles) > 0:
            return render_template('articles.html',articles=articles)
        else:
            msg = 'No Articles Found'
            return render_template('articles.html', msg = msg)
    # Close Connection      
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    cur = cnx.cursor(buffered=True,dictionary=True)

    # Get Article
    cur.execute('SELECT * FROM articles where id = %s', [id])
    article = cur.fetchone()
       
    return render_template('article.html', article  = article)
    


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1,max=50)])
    username = StringField('User Name', [validators.Length(min=4,max=25)])
    email = StringField('Email', [validators.Length(min=6,max=50)])
    password = PasswordField('Password', [validators.DataRequired(),
                    validators.EqualTo('confirm', message= 'Password do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods = ['GET',"POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Get a cursor
        cur = cnx.cursor(dictionary=True)

        #Execute query
        cur.execute('INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)',(name,email,username,password))

        # save chanes to database 
        cnx.commit()

        #close connection
        cur.close()

        #flash msg for register
        flash('You are now register and can login', 'success')

        return redirect(url_for('login'))

        #return render_template('register.html')
    return render_template('register.html', form=form) 

@app.route('/login', methods=['POST', 'GET'])
def login():


    if request.method == 'POST':
       #get form fields 
       username = request.form['username']
       password_candidate = request.form['password']

       #create cursor
       cur = cnx.cursor(buffered=True,dictionary=True)
       # Get user by username
       cur.execute('SELECT * FROM users WHERE username = %s',[username])
       result = cur.fetchone()
       
       if result is not None:

           print(result,"result")
           if  len(result) > 0:   # if there is any row found
             #get store data
                password = result['password']   

           #compare password
                if sha256_crypt.verify(password_candidate, password):
                    # passed
                    session['logged_in'] = True
                    session['username'] = username

                    flash('you are now logged in', 'success')
                    return redirect(url_for('dashboard'))                             
                    
                else:
                    error = 'invalid login '
                    return render_template('login.html', error=error)
                    # close connection
                cur.close()
               
       else:
           error = 'User-Name not found'
           return render_template('login.html', error=error)

    return render_template('login.html') 

# Check if user logged in
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
        
    return wrap
      
                          
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():

    cur = cnx.cursor(buffered=True,dictionary=True)

    # Get Articles
    cur.execute('SELECT * FROM articles')
    articles = cur.fetchall()
       
    if articles is not None:

        if len(articles) > 0:
            return render_template('dashboard.html',articles=articles)
        else:
            msg = 'No Articles Found'
            return render_template('dashboard.html', msg = msg)
    # Close Connection      
    cur.close()


# Article Form Class for validation
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1,max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#ADD Article route
@app.route('/add_article', methods = ['POST','GET'])
@login_required
def add_article():
    form=ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = cnx.cursor()
        #Execute
        cur.execute('INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)',(title,body,session['username']))

        # save chanes to database 
        cnx.commit()

        #close connection
        cur.close()

        #flash msg for register
        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)


#Edit Article route
@app.route('/edit_article/<string:id> ', methods = ['POST','GET'])
@login_required
def edit_article(id):

    # Create cursor
    cur = cnx.cursor(dictionary=True)

    # CREATE EXECUTE
    cur.execute('select * from articles where id= %s',[id])
    #Get article
    article = cur.fetchone()


    form=ArticleForm(request.form)
# Populate article form fields....we get this from database
    form.title.data = article['title']
    form.body.data = article['body']


    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create cursor
        cur = cnx.cursor(dictionary=True)
        #Execute
        cur.execute('update articles set name =%s, body = %s where id = %s',(title,body,id))

        # save chanes to database 
        cnx.commit()

        #close connection
        cur.close()

        #flash msg for update
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template("edit_article.html", form=form)

@app.route('/delete_article/<string:id>', methods =['POST','GET'])
@login_required
def delete_article(id):

    # Create cursor
    cur = cnx.cursor()
        #Execute
    cur.execute('DELETE FROM articles where id = %s', [id])

        # save chanes to database 
    cnx.commit()

        #close connection
    cur.close()

        #flash msg for register
    flash('Article Updated', 'success')
    return redirect(url_for('dashboard'))



if __name__ == "__main__":
    app.secret_key = '123456'

    app.run(debug = True)   