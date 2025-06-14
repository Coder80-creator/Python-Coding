# app.py
from flask import Flask, render_template, request
from scraper import scrape_all_sites

# Initialize the Flask application
app = Flask(__name__)


# Define the main route for the application
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles requests to the home page.
    - On GET request: Displays the initial form.
    - On POST request: Takes the product name from the form,
      calls the scraper to get results, and renders the results.
    """
    # Initialize results dictionary with empty lists for Amazon and eBay
    results = {'amazon': [], 'ebay': []}

    # Check if the request method is POST (i.e., the search form was submitted)
    if request.method == 'POST':
        # Get the product name from the submitted form data
        product_name = request.form['product_name']

        # Call the scrape_all_sites function from scraper.py
        # This function will return a dictionary with 'amazon' and 'ebay' keys
        results = scrape_all_sites(product_name)

    # Render the index.html template, passing the results dictionary to it
    return render_template('index.html', results=results)


# This block ensures the Flask app runs when the script is executed directly
if __name__ == '__main__':
    # Run the Flask application in debug mode.
    # Debug mode provides detailed error messages and automatically reloads
    # the server on code changes.
    app.run(debug=True)
