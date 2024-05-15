from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import yaml
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'justin_secret_key'
# Configure MySQL from YAML file
db_config = yaml.load(open('db.yaml'), Loader=yaml.SafeLoader)
app.config['MYSQL_HOST'] = db_config['mysql_host']
app.config['MYSQL_USER'] = db_config['mysql_user']
app.config['MYSQL_PASSWORD'] = db_config['mysql_password']
app.config['MYSQL_DB'] = db_config['mysql_db']

mysql = MySQL(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM User WHERE Name = %s AND Password = %s", (name, password))
        user = cur.fetchone()
        cur.close()
        print(user)
        if user:
            session['userid'] = user[0]
            session['name'] = user[1]
            session['taste'] = user[2]
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid Username or Password.")
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        taste = request.form['taste']
        password = request.form['password']
        confirm = request.form['confirm']

        if len(name) == 0 or len(password) == 0 or len(taste) == 0:
            # If any textbox is empty, redirect back to register page with an error message
            return render_template('signup.html', error='Some required fields are empty.')
        elif password != confirm:
            # If passwords do not match, redirect back to register page with an error message
            return render_template('signup.html', error='Passwords do not match.')
    
        cur = mysql.connection.cursor()
        cur.execute("SELECT MAX(UserId) FROM User")
        curId = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO User (UserId, Name, Taste, Password) VALUES (%s, %s, %s, %s)", (curId, name, taste, password))

        mysql.connection.commit()
        cur.close()
        return render_template('login.html', message='Successfully Registered! Welcome to HangOut!')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('userid', None)
    session.pop('name', None)
    session.pop('taste', None)
    return redirect(url_for('login'))


@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if 'userid' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        restaurant_name = request.form['restaurantName']
        stars = float(request.form['stars'])
        review_text = request.form['text']

        if stars < 0 or stars > 5:
            flash('Invalid star rating. Please provide a value between 0 and 5.')
            return redirect(url_for('add_review'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT RestaurantId FROM Restaurant WHERE RestaurantName = %s", (restaurant_name,))
        restaurant = cur.fetchone()
        if restaurant is None:
            flash('Restaurant does not exist.')
            return redirect(url_for('add_review'))

        # Fetch the current average stars
        cur.execute("SELECT AVG(Stars) FROM Review WHERE RestaurantId = %s", (restaurant[0],))
        avg_stars_before = cur.fetchone()[0] or 0

        # Insert the new review
        current_time = datetime.now()
        cur.execute("INSERT INTO Review (RestaurantId, UserId, Stars, Text, Date) VALUES (%s, %s, %s, %s, %s)",
                    (restaurant[0], session['userid'], stars, review_text, current_time))
        mysql.connection.commit()

        # Fetch the updated average stars
        cur.execute("SELECT AVG(Stars) FROM Review WHERE RestaurantId = %s", (restaurant[0],))
        avg_stars_after = cur.fetchone()[0]

        cur.execute("select Text from Review where RestaurantId = %s and UserId = %s and Stars = %s", (restaurant[0], session['userid'], stars))
        cur_text = cur.fetchone()[0]
        # print(cur.execute("select Text from Review where RestaurantId = %s", (restaurant[0])))

        cur.close()

        # Send back the results to the template
        return render_template('review_added.html', 
                               restaurant_name=restaurant_name, 
                               review_text=cur_text,
                               avg_stars_before=avg_stars_before,
                               avg_stars_after=avg_stars_after)
    
    return render_template('add_review.html')

@app.route('/search_restaurant', methods=['GET', 'POST'])
def search_restaurant():
    if request.method == 'POST':

        # Modified SQL query to group by restaurant name and select distinct names
        sql_restaurant_search = """
        SELECT Distinct
            (RestaurantName) AS RestaurantName, (Category) AS Category, (City) AS City,
            (Hours) AS Hours, (Stars) AS Stars, (PostalCode) AS PostalCode,
            (State) AS State, (Latitude) AS Latitude, (Longitude) AS Longitude,
            (Count) AS Count, (Cleared) AS Cleared
        FROM
            Location L NATURAL JOIN Restaurant R NATURAL JOIN Crime C
        WHERE
            Category LIKE %s AND City LIKE %s AND Stars >= %s

        """
        
        results = []

        # Defaults are inclusive
        category = request.form.get('category', "")
        city = request.form.get('city', "")
        stars = request.form.get('stars', 0)

        params = [f"%{category}%", f"%{city}%", stars]

        # Default values make a distinction
        restaurant_name = request.form.get('restaurant_name', None)
        postal_code = request.form.get('postal_code', None)
        crime_count = request.form.get('crime_count', None)

        if restaurant_name:
            sql_restaurant_search += " AND RestaurantName = %s"
            params.append(restaurant_name)

        if postal_code:
            sql_restaurant_search += " AND PostalCode LIKE %s"
            params.append(postal_code)

        if crime_count:
            sql_restaurant_search += " AND Count <= %s"
            params.append(crime_count)
        sql_restaurant_search+=" Limit 1"

        # fetch data
        cur = mysql.connection.cursor()
        cur.execute(sql_restaurant_search, params)
        results = cur.fetchall()
        cur.close()

        return render_template('search_restaurant_results.html', results=results)

    else:
        return render_template('search_restaurant.html')


# stored procedure
@app.route('/search_dish', methods=['GET', 'POST'])
def search_dish():

    if request.method == 'POST':

        dishName = request.form.get('dishName', None)

        if dishName == None or type(dishName) != str:
            return 'Dish name is missing/invalid'
        
        cur = mysql.connection.cursor()
        cur.callproc('WithDishRestaurantInfo', [dishName])

        crime_type = dict()
        crime_type[0] = 'Theft/Larceny'
        crime_type[1] = 'Burglary'
        crime_type[2] = 'Robbery'
        crime_type[3] = 'Assault'
        crime_type[4] = 'Homicide'
        crime_type[5] = 'Drug Trafficking'
        crime_type[6] = 'Kidnapping'

        crime_results = []
        restaurant_results = []

        # fetch restaurant
        results = cur.fetchall()
        if not results:
            return render_template('search_dish_results.html', dishName = dishName, restaurant_results=[], crime_results=[])
        # restaurant_results.append(results)
        for result in results:
            restaurant_results.append(result)
        # fetch crime
        cur.nextset()
        results = cur.fetchall()
        crime_results.append(results)
        
        while cur.nextset():
            results = cur.fetchall()
            for result in results:
                restaurant_results.append(result)
            cur.nextset()
            results = cur.fetchall()
            crime_results.append(results)

        cur.close()
        return render_template('search_dish_results.html', dishName = dishName, restaurant_results=restaurant_results, crime_results=crime_results)
    
    else:
        return render_template('search_dish.html')


def is_insert_dish():
    return 'dish_id_add' in request.form and 'restaurant_id_add' in request.form and 'price_add' in request.form and 'name_add' in request.form

def is_delete_dish():
    return 'dish_id_del' in request.form and 'restaurant_id_del' in request.form

def is_update_dish():
    return 'dish_id_upd' in request.form and 'restaurant_id_upd' in request.form and 'price_upd' in request.form



@app.route('/modify_dish_data', methods=['GET', 'POST'])
def modify_dish_data():

    if request.method == 'POST':

         # Case: Insert Dish
        if is_insert_dish():
            print('in insert dish')

            dish_details = request.form
            dish_id = dish_details['dish_id_add']
            restaurant_id = dish_details['restaurant_id_add']
            price = dish_details['price_add']
            name = dish_details['name_add']

            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO Dish (DishId, RestaurantId, Price, Name) VALUES (%s, %s, %s, %s)",
                (dish_id, restaurant_id, price, name)
            )
            mysql.connection.commit()
            cur.close()

            return redirect('/all_dishes')
        
        # Case: Delete Dish
        elif is_delete_dish():
            print('in delete dish')

            dish_id = request.form.get('dish_id_del')
            restaurant_id = request.form.get('restaurant_id_del')

            print("Restaurant ID:", restaurant_id)
            print("Dish ID:", dish_id)

            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM Dish WHERE RestaurantId = %s AND DishId = %s", (restaurant_id, dish_id))
            mysql.connection.commit()
            cur.close()
            
            return redirect('/all_dishes')

        # Case: Update Dish
        elif is_update_dish():
            print('in update dish')

            dish_id = request.form['dish_id_upd']
            restaurant_id = request.form['restaurant_id_upd']
            new_price = request.form['price_upd']

            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE Dish SET Price = %s WHERE DishId = %s AND RestaurantId = %s",
                (new_price, dish_id, restaurant_id)
            )
            mysql.connection.commit()
            cur.close()

            return redirect('/all_dishes')
        
        return render_template('modify_dish_data.html')

    return render_template('modify_dish_data.html')


@app.route('/all_dishes', methods=['GET', 'POST'])
def list_all_dishes():

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Dish")
    all_dishes = cur.fetchall()
    cur.close()

    return render_template('all_dishes.html', dishes=all_dishes)

@app.route('/transaction', methods=['GET', 'POST'])
def transaction_get_restaurant_info_with_crime():

    if request.method == 'POST':

        location_name = request.form.get('location_name', None)
        min_rating = request.form.get('min_rating', None)

        if location_name == None or type(location_name) != str:
            return 'location name is missing/invalid'

        if min_rating == None:
            return 'min rating is missing'
        
        try:
            min_rating = float(min_rating)
        except Exception as e:
            return "min_rating is invalid"
        
        cur = mysql.connection.cursor()
        cur.callproc('GetRestaurantInfoWithCrime', [location_name, min_rating])

        crime_type = dict()
        crime_type[0] = 'Theft/Larceny'
        crime_type[1] = 'Burglary'
        crime_type[2] = 'Robbery'
        crime_type[3] = 'Assault'
        crime_type[4] = 'Homicide'
        crime_type[5] = 'Drug Trafficking'
        crime_type[6] = 'Kidnapping'

        crime_results = []
        restaurant_results = []

        # restaurant results
        results = cur.fetchall()
        for result in results:
            restaurant_results.append(result)

        # crime results
        if cur.nextset():
            results = cur.fetchall()
            for result in results:
                crime_results.append((crime_type[result[0]], result[1]))

        # # restaurant results
        # count = 0
        # while cur.nextset():
        #     if count == 0:
        #         results = cur.fetchall()
        #         for result in results:
        #             restaurant_results.append(result)
        #         count = 1
        #     else:
        #         count = 0

        print('restaurant_results: ', restaurant_results)
        print('crime_results: ', crime_results)
        
        cur.close()
        return render_template('transaction_results.html', location_name = location_name, min_rating = min_rating, restaurant_results=restaurant_results, crime_results=crime_results)
    
    else:
        return render_template('transaction.html')




@app.route('/')
def index():
    # Check if user is logged in
    if 'userid' in session:
        # User logged in, display the main page
        return render_template('index.html', name=session['name'])
    else:
        # User not logged in, redirect to login page
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
