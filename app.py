from flask import Flask, request, send_file, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import tempfile
import time

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url' in request."}), 400

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(3)

        top_swatch_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-attribute="pa_top-color"]')
        bottom_swatch_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-attribute="pa_bottom-color"]')

        output_rows = []

        for top_div in top_swatch_divs:
            try:
                top_link = top_div.find_element(By.TAG_NAME, 'a')
                top_color = top_div.get_attribute("data-value")
                driver.execute_script("arguments[0].click();", top_link)
                time.sleep(1.5)

                for bottom_div in bottom_swatch_divs:
                    try:
                        bottom_link = bottom_div.find_element(By.TAG_NAME, 'a')
                        bottom_color = bottom_div.get_attribute("data-value")
                        driver.execute_script("arguments[0].click();", bottom_link)
                        time.sleep(2.5)

                        image = driver.find_element(By.CSS_SELECTOR, 'div.woocommerce-product-gallery__image img.wp-post-image')
                        image_url = image.get_attribute("src")
                        output_rows.append([top_color, bottom_color, image_url])

                    except Exception as e:
                        output_rows.append([top_color, bottom_color, f"Error: {e}"])
            except Exception as e:
                output_rows.append([f"Error: {e}", "", ""])

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='')
        writer = csv.writer(tmp_file)
        writer.writerow(["Top Color", "Bottom Color", "Image URL"])
        writer.writerows(output_rows)
        tmp_file.close()

        return send_file(tmp_file.name, mimetype='text/csv', as_attachment=True, download_name='color_combinations.csv')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)
