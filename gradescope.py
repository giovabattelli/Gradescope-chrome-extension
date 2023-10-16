# Import necessary libraries
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, request
from flask_cors import cross_origin
from selenium import webdriver
from bs4 import BeautifulSoup
import html
import re


#Use email and password data from popup.js to login to Gradescope
app = Flask(__name__)

def image_parser(main_content):
    #Sort and parse for image links
    background_images = main_content.find_all(style=re.compile(r'background-image:\s*url\([^)]+\)'))
    image_pattern = r'https://[^"]+'
    result_images = []
    #Parse images
    for image in background_images:
        url = re.findall(image_pattern, image['style'])
        url = [html.unescape(u) for u in url]
        result_images.extend(url)
    return result_images

# Function to parse problem numbers
def problem_number_parser(soup, max_problem_length=6):
    result_problems = []
    problem_outline = soup.find_all('div', class_='selectPagesQuestionOutline--title')
    problem_pattern = r'</strong>(.*?)</div>'
    for problem in problem_outline:
        num = re.search(problem_pattern, str(problem))
        num_parsed = num.group(1).strip()
        if len(num_parsed) <= max_problem_length:
            result_problems.append(num_parsed)
    return result_problems


@app.route('/get-data', methods=['POST'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_data():
    received_data = request.json
    email = received_data.get('email')
    password = received_data.get('password')

    print(email)
    print(password)

    # Setup selenium driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    # Automate sign-in process
    driver.get("https://www.gradescope.com/login")
    driver.find_element_by_id("session_email").send_keys(email)
    driver.find_element_by_id("session_password").send_keys(password)
    driver.find_element_by_name("commit").click()

    # Wait until the page loads
    WebDriverWait(driver, timeout=10).until(lambda x: x.execute_script("return document.readyState === 'complete'"))

    # Access and parse content
    driver.get("https://www.gradescope.com/courses/567436/assignments/3290069/submissions/193818048/select_pages")
    html_content = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html_content, "html.parser")
    main_content = soup.find("main")

    # Use the parsing functions
    image_links = image_parser(main_content)
    problem_numbers = problem_number_parser(soup)

    # Print the results
    print(image_links)
    print(problem_numbers)

    return jsonify({"status": "success", "image_links": image_links, "problem_numbers": problem_numbers})

if __name__ == '__main__':
    app.run(port=5000)
