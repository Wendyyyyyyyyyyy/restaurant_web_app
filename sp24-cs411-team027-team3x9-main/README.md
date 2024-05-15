# Restaurant Review Application

## sp24-cs411-team027-team3x9


This Flask-based web application allows users to sign up, log in, and manage their profiles, as well as review restaurants and search for restaurants and dishes based on various criteria.

## Features

### User Authentication
- **Sign Up**: Users can create a new account by providing a username, password, and their taste preferences.
- **Login**: Users can log in using their credentials.
- **Logout**: Allows users to log out of the application.

### Restaurant Reviews
- **Add Review**: Logged-in users can add reviews for restaurants, including a star rating and text.
- **Search Restaurant**: Users can search for restaurants based on category, city, and minimum star rating. Additional filters include restaurant name, postal code, and crime rate in the area.

### Dish Management
- **Search Dish**: Search for dishes by name across different restaurants and retrieve related crime data.
- **Modify Dish Data**: Users with appropriate permissions can add, delete, or update dish details in the database.
- **List All Dishes**: Displays all dishes in the database.

### Advanced Features
- **Transaction**: Demonstration of a complex transaction in SQL, retrieving detailed information about restaurants and associated crime data based on location and rating filters.

## Setup

### Prerequisites
- Python 3.x
- Flask
- Flask-MySQLdb
- PyYAML
- A MySQL server

### Installation
1. Clone the repository:
```
git clone [repository_url]
cd [repository_directory]
```
2. Install dependencies:
```
pip install flask flask-mysqldb pyyaml werkzeug
```
3. Configure the database:
- Modify the `db.yaml` file under the project directory to include your MySQL database credentials.

### Running the Application
1. Start the Flask application:
```
python app.py
```
2. Open a web browser and navigate to `http://127.0.0.1:5000/` to access the application.

## Usage
- **Home Page**: Accessible at the root URL (`/`). Redirects to the login page if the user is not logged in.
- **Login/Signup**: Use the login/signup forms to access user-specific functionalities.
- **Review and Search**: After logging in, users can add reviews, search for restaurants, and manage dish data through the navigation menu.

## Required Advanced SQL Commands


```
DELIMITER //
CREATE PROCEDURE GetRestaurantInfoWithCrime(
    IN location_name VARCHAR(31),
    IN min_rating REAL
)
BEGIN
    -- Declare variable to check if valid restaurants exist
    DECLARE valid_restaurant_exists BOOLEAN DEFAULT FALSE;
    -- Start the transaction
    START TRANSACTION;
    -- Check if the input min_rating is within a valid range
    IF min_rating >= 0 AND min_rating <= 5 THEN
        -- Query to get restaurant information based on location and minimum rating
        SELECT r.RestaurantName, AVG(rev.Stars) AS AvgRating
        FROM Restaurant r
        INNER JOIN Review rev ON r.RestaurantId = rev.RestaurantId
        INNER JOIN Location loc ON r.LocationId = loc.LocationId
        WHERE loc.City = location_name
        GROUP BY r.RestaurantId
        HAVING AvgRating >= min_rating
        ORDER BY AvgRating DESC;
         SELECT c.Type AS Crime_Type, COUNT(*) AS Crime_Count
         FROM Crime c
         INNER JOIN Location loc ON c.LocationId = loc.LocationId
         WHERE loc.City = location_name
         GROUP BY c.Type;
    ELSE
        -- If min_rating is not valid, output an error or a specific message
        SELECT 'Invalid rating. Please provide a rating between 0 and 5.' AS ErrorMessage;
    END IF;
    -- Commit the transaction
    COMMIT;
END //
DELIMITER ;

```

```
DELIMITER //

CREATE TRIGGER set_default_review_text
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
    IF TRIM(NEW.Text) IS NULL OR TRIM(NEW.Text) = '' THEN
        IF NEW.Stars >= 4 THEN
            SET NEW.Text = 'System default Great';
        ELSEIF NEW.Stars BETWEEN 2 AND 3 THEN
            SET NEW.Text = 'System default Normal';
        ELSE
            SET NEW.Text = 'System default Bad';
        END IF;
    END IF;

    -- Additionally, update the average star rating in the Restaurant table
    UPDATE Restaurant
    SET Stars = (SELECT AVG(Stars) FROM Review WHERE RestaurantId = NEW.RestaurantId)
    WHERE RestaurantId = NEW.RestaurantId;
END;

//
DELIMITER ;
```

```
DELIMITER $$
CREATE PROCEDURE WithDishRestaurantInfo(
    IN dishName VARCHAR(127)
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE vRestaurantId INT;
    DECLARE vRestaurantName VARCHAR(255);
    DECLARE vCity VARCHAR(127);
    DECLARE vState VARCHAR(127);
    DECLARE cur CURSOR FOR
        SELECT
            r.RestaurantId,
            r.RestaurantName,
            l.City,
            l.State
        FROM Dish d
        LEFT JOIN Restaurant r ON d.RestaurantId = r.RestaurantId
        LEFT JOIN Location l ON r.LocationId = l.LocationId
        WHERE d.Name LIKE CONCAT('%', dishName, '%');
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    -- Check if the input dish name is not empty
    IF TRIM(dishName) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dish name cannot be empty';
    ELSE
        OPEN cur;
        read_loop: LOOP
            FETCH cur INTO vRestaurantId, vRestaurantName, vCity, vState;
            IF done THEN
                LEAVE read_loop;
            END IF;
            -- Output current restaurant information
            SELECT vRestaurantId, vRestaurantName, vCity, vState;
            -- Execute second query for the current restaurant
            SELECT
                c.Type AS CrimeType,
                SUM(c.Count) AS TotalIncidents,
                AVG(c.Count) AS AverageIncidents
            FROM Crime c
            JOIN Occurrence o ON c.CrimeId = o.CrimeId
            JOIN Restaurant r ON r.RestaurantId = o.RestaurantId
            WHERE r.RestaurantId = vRestaurantId
            GROUP BY c.Type
            ORDER BY TotalIncidents DESC;
        END LOOP;
        CLOSE cur;
    END IF;
END$$
DELIMITER ;
```
