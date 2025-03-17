# Top-K Hotel Recommendation Using R-Tree 

## Table of Contents
1. [Project Description](#project-description)
2. [Dataset Information](#dataset-information)
3. [Installation Guide](#installation-guide)
4. [Usage Instructions](#usage-instructions)
   - [Data Preprocessing](#data-preprocessing)
   - [Top-K Algorithm Implementation](#top-k-algorithm-implementation)
   - [Visualization](#visualization)
5. [Additional Information](#additional-information)

## Project Description
This project implements a **Top-K hotel recommendation system** using the **R-Tree spatial index**. The system finds the **K best hotels** based on user-defined preferences, including:

- **Geographic distance** from a reference location
- **Hotel rating** (quality assessment)
- **Number of reviews** (popularity indicator)

Users can specify weight preferences for each criterion, and the system calculates an overall score using a **weighted sum function**. The results are presented both as a **textual list** and as an **interactive map**.

## Dataset Information
- **Dataset Used**: TripAdvisor Hotels Greece (Kaggle)
- **File Format**: CSV
- **Features**:
  - `latitude`, `longitude` (Geographic coordinates)
  - `hotel_name` (Hotel name)
  - `rating` (Hotel rating)
  - `number_of_reviews` (Number of reviews)

## Installation Guide
### Prerequisites
Ensure you have **Python 3.x** installed.

### Required Libraries
Run the following command to install the necessary dependencies:
```sh
pip install pandas geopandas rtree shapely folium
```

## Usage Instructions

### Data Preprocessing
1. Load the dataset (CSV file containing hotel data).
2. Convert geographic coordinates into spatial objects using **GeoPandas**.
3. Construct an **R-Tree** index for efficient spatial queries.

### Top-K Algorithm Implementation
1. **User Input:** Enter the reference location (`latitude`, `longitude`), number of results (`K`), and weight preferences for distance, rating, and number of reviews.
2. **Normalization:** Convert all features to a scale of `[0,1]`.
3. **Score Calculation:** Compute the weighted sum score:
   ```
   score = wd * (1 - normalized_distance) + wr * normalized_rating + wn * normalized_reviews
   ```
   - Smaller distances contribute positively to the score.
   - Larger ratings and number of reviews contribute positively.
4. **Sorting & Selection:** Rank hotels based on score and return the **Top-K**.

### Visualization
- The **Top-K hotels** are displayed on an **interactive map** using **Folium**.
- Different markers represent:
  - **Reference location** (Blue)
  - **All hotels** (Green)
  - **Top-K hotels** (Red)
- The map is saved as an **HTML file** and can be opened in any browser.

## Additional Information
- The dataset and code are structured to allow **easy extension** (e.g., adding more filters or features).
- Performance is optimized using the **R-Tree** spatial index for fast location-based queries.
