# Database Design Specification

## Assumptions

### User
- **UserId**: Unique identifier. Cannot be modified.
- **Password**: Can be updated.
- **Taste**: Preferred taste. Can be updated.
- **Name**: Does not need to be unique. Cannot be modified.

### Restaurant
- **RestaurantId**: Unique identifier.
- **RestaurantName**: May not be unique.
- **Stars**: Rating on a scale of 1 to 5.
- **Hours**: Opening hours.
- **Category**: Type of cuisine (e.g., Chinese, Indian).
- **Location**: Must belong to a specific location.

### Review
- **ReviewId**: Unique identifier.
- **Text**: Review content.
- **Stars**: Rating given by the user.
- **Date**: Date of the review.
- **UserId**: Identifier of the user who wrote the review.
- **RestaurantId**: Identifier of the restaurant reviewed.

### Crime
- **CrimeId**: Unique identifier.
- **CrimeType**: Type of crime. Multiple records can have the same type.
- **Neighbourhood**: Location of the crime.
- **Count**: Number of crime events. Must be larger than 0.

### Dish
- **DishId**: Unique identifier.
- **Name**: May not be unique.
- **Price**: Cost of the dish.
- **Restaurant**: Must belong to a specific restaurant.

### Location
- **LocationId**: Unique identifier, needed since that City, State, PostalCode, or Lattitude and Longitude (as seen in the given data) might not be unique, and that Neightborhood cannot uniquely identify PostalCode or Lattitude and Longitude.
- **Latitude** and **Longitude**: Geographic coordinates.
- **City**, **State**, **PostalCode**, **Neighborhood**: Location details.

## Entity Description

### Restaurant

- RestaurantId: Unique identifier for each restaurant in our database
- RestaurantName: The name of the restaurant
- Stars: The rating of the restaurant, on a scale of 1 to 5.
- Hours: Hours when the restaurant opens.
- Category: Type of cuisine the restaurant serves (eg. Chinese, Indiana, etc)

### Crimes

- CrimeId: Unique identifier for each row (a set of crimes with the same type)
- Neighborhood: The location of the crimes 
- Count: The number of crime events.
- Cleared: The number of crime events that have been cleared by local police.
- Category: The type of crime (eg. robbery, violent-crime etc)

### Location

- LocationId: Unique identifier for each location.
- Neighborhood: The community: jurisdiction belongs to which local police station.
- PostalCode: The postal code.
- Latitude: The latitude.
- Longitude: The longitude.
- City: The city where the location is located.
- State: The state where the location is located.

### Dish

- DishId: Unique identifier for each dish.
- Price: The price of the dish.
- Name: The name of the dish.

### User

- UserId: Unique identifier for each user.
- Name: The name of the user.
- Password: The password of the user.
- Taste: The preference of a user based on his reviews/dining history.



## Relations

### HappensAround
- Crime events happen around the restaurants In the crime table, each row represents a number of crime events with the same type near a specific location. Therefore, for each row in crime, it could be near zero or one or more restaurants. Similarly, for each restaurant, it could be near zero or one or more crime locations. Therefore, there is a zero or many to zero or many relationship between Restaurants entity and Crimes entity. 

### Has
- A restaurant serves different dishes. For each restaurant, it could possibly serve one or more dishes. It could also have zero dish in our database, which indicates we do not have any information about the dish about this particular restaurant. In contrast, for each dish, it cannot exist without the restaurant. (There is an underlying assumption that although different restaurants could name a cuisine exactly the same name, we still recognize them as internally different as they do have independent recipes and attributes such as prices.) Therefore, we have a one to zero or many relationship between the Restaurant entity and the Dish entity.

### At (Restaurant and Location)
- A restaurant has its location. For each restaurant, it can only have exactly one locations. However, several restaurants can share the same location since there might be some shopping mall or food court containing one than one restaurants. In addition, there is also another possibility that we have a location which is stored in our crime data base but there is no restaurants in that region. Therefore, there is an exactly one to zero or many relationship between Restaurants entity and Crimes entity.

### At (Crime and Location)
- A Crimes has its location. For each Crime, it can only have exactly one locations. However, several Crimes can share the same location. In addition, there is also another possibility that we have a location which is stored in our restaurant data base but there is no Crime in that region.  Therefore, there is a zero or many to one relationship between Crimes entity and Location entity. 

### Review
- Restaurants are reviewed by users. Each user can have zero or multiple reviews, and a restaurant can also has many reviews or no reviews at all (maybe it’s new). A review should contain text (the thoughts of the customers), the star (0~5, the overall rating), and the review time. 
