import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from rtree import index
import folium
import math

#Load data from a CSV file
#The dataset contains hotel information for Greece from TripAdvisor
tripadvisor_df = pd.read_csv("tripadvisor_hotels_greece_202210.csv")

#Create geometry (geographic points) for the hotels in the dataset
#Adds a 'geometry' column containing Point objects for each hotel
tripadvisor_df['geometry'] = tripadvisor_df.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)

#Convert the DataFrame to a GeoDataFrame for spatial analysis
tripadvisor_gdf = gpd.GeoDataFrame(tripadvisor_df, geometry='geometry')

#Build an R-tree index
#Used for fast lookup of points near the reference point
rtree_idx = index.Index()
for idx, row in tripadvisor_gdf.iterrows():
    if isinstance(row['geometry'], Point): #Ensure the geometry is a valid Point
        #Insert the point into the R-tree in the form (x_min, y_min, x_max, y_max)
        rtree_idx.insert(idx, (row['geometry'].x, row['geometry'].y, row['geometry'].x, row['geometry'].y))

#Function to calculate the Euclidean distance between two points
def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

#Function to normalize values to the range [0, 1]
#Ensures feature values are comparable
def normalize(value, min_value, max_value):
    if max_value - min_value == 0: #Avoid division by zero
        return 0
    return (value - min_value) / (max_value - min_value)

#Modified distance normalization
#Applies an inverse scaling to emphasize closer points
def normalize_distance(distance, max_distance):
    if max_distance == 0: #Avoid division by zero
        return 0
    return 1 - (distance / max_distance) #Inverts values to prioritize shorter distances

#Function to calculate the final score for each hotel
def calculate_score(distance, rating, num_reviews, weight_distance, weight_rating, weight_reviews, min_distance, max_distance, min_rating, max_rating, min_reviews, max_reviews):
    #Normalize distance, rating, and number of reviews to [0, 1]
    norm_distance = normalize(distance, min_distance, max_distance)
    norm_rating = normalize(rating, min_rating, max_rating)
    norm_reviews = normalize(num_reviews, min_reviews, max_reviews)

    #Apply penalty to longer distances
    #This enhances the difference between near and far points
    penalized_distance = (1 - norm_distance) ** 2 #Exaggerates the difference between nearby and far points

    #Calculate the final score using user-defined weights
    return weight_distance * penalized_distance + weight_rating * norm_rating + weight_reviews * norm_reviews

#Function to find the Top-k points based on the given weights
def top_k_query_with_rtree(tripadvisor_gdf, ref_point, k, weight_distance, weight_rating, weight_reviews, max_allowed_distance_km=1.0):
    scores = [] #List to store the scores for each candidate

    #Find candidate points using the R-tree
    candidate_indices = list(rtree_idx.nearest((ref_point[0], ref_point[1], ref_point[0], ref_point[1]), num_results=len(tripadvisor_gdf)))

    #Calculate scores for each candidate
    for idx in candidate_indices:
        row = tripadvisor_gdf.iloc[idx]
        point = row['geometry']

        if isinstance(point, Point):
            #Calculate the distance to the reference point
            dist = calculate_distance(ref_point, (point.x, point.y))
            if weight_distance > 0 and dist > max_allowed_distance_km: #Filter based on distance if it has weight
                continue

            #Retrieve rating and number of reviews
            rating = row['rating'] if pd.notnull(row['rating']) else 0
            num_reviews = row['num_reviews'] if pd.notnull(row['num_reviews']) else 0
            name = row['name'] if 'name' in row else "Unknown Name"
            website = row.get('website', 'No Website')

            #Ignore distance if rating or reviews have 100% weight
            if weight_rating == 1.0:
                norm_dist = 0 #Ignore distance
                norm_reviews = num_reviews / max(tripadvisor_gdf['num_reviews'].fillna(0))
                norm_rating = rating / 5.0
            elif weight_reviews == 1.0:
                norm_dist = 0 #Ignore distance
                norm_reviews = num_reviews / max(tripadvisor_gdf['num_reviews'].fillna(0))
                norm_rating = 0
            else:
                #Normalize all values
                norm_dist = dist / max_allowed_distance_km
                norm_reviews = num_reviews / max(tripadvisor_gdf['num_reviews'].fillna(0))
                norm_rating = rating / 5.0

            #Calculate the score
            score = ((1 - norm_dist) * weight_distance + norm_rating * weight_rating + norm_reviews * weight_reviews) / 1.0 #Normalize the final result

            #Append the point to the scores list
            scores.append((point.x, point.y, dist, name, rating, num_reviews, website, score))

    #Sort the points based on their scores in descending order
    scores.sort(key=lambda x: x[7], reverse=True)
    return scores[:k]

#Input the reference point from the user
ref_long = float(input("Enter the longitude of the reference point: "))
ref_lat = float(input("Enter the latitude of the reference point: "))
ref_point = (ref_long, ref_lat)

#Input the number of top results (k)
k = int(input("Enter the number of top points (k): "))

#Input weights for distance, rating, and reviews
weight_distance = float(input("Enter weight for distance (%): ")) / 100
weight_rating = float(input("Enter weight for rating (%): ")) / 100
weight_reviews = float(input("Enter weight for number of reviews (%): ")) / 100

#Check that the weights sum to 100%
if not math.isclose(weight_distance + weight_rating + weight_reviews, 1.0, rel_tol=1e-9):
    raise ValueError("The sum of weights must equal 100%")

#Execute the Top-k query and get the results
top_k_points = top_k_query_with_rtree(tripadvisor_gdf, ref_point, k, weight_distance, weight_rating, weight_reviews)

#Print the results
print("Top-k Points:")
for point in top_k_points:
    print(f"Name: {point[3]}, Rating: {point[4]}, Reviews: {point[5]}, Distance: {point[2]:.2f} km, Score: {point[7]:.2f}")

#Create an interactive map using Folium
m = folium.Map(location=[ref_lat, ref_long], zoom_start=14)

#Add all hotels to the map
for idx, row in tripadvisor_gdf.iterrows():
    point = row['geometry']
    if isinstance(point, Point):
        name = row['name'] if 'name' in row else "Unknown Name"
        rating = row.get('rating', 'N/A')
        num_reviews = row.get('num_reviews', 'N/A')

        folium.Marker(location=[point.y, point.x], popup=(f"Name: {name}<br>Rating: {rating}<br>Reviews: {num_reviews}"), icon=folium.Icon(color="green")).add_to(m)

#Add the Top-k points to the map
for point in top_k_points:
    folium.Marker(
        location=[point[1], point[0]],
        popup=(f"Name: {point[3]}<br>Rating: {point[4]}<br>Reviews: {point[5]}<br>Distance: {point[2]:.2f} km"), icon=folium.Icon(color="red")).add_to(m)

#Add the reference point to the map
folium.Marker(location=[ref_lat, ref_long], popup="Reference Point", icon=folium.Icon(color="blue")).add_to(m)

#Save the map to an HTML file
m.save("top_k_map_with_reference_tripadvisor.html")
print("The map has been saved as 'top_k_map_with_reference_tripadvisor.html'.Open it in a browser to view.")
