import cv2
import pytesseract
import os
import requests
from flask import Flask, request, jsonify
from queue import Queue
from threading import Thread
from io import BytesIO
import numpy as np
import urllib.request
import requests
import json

app = Flask(__name__)
image_queue = Queue()

# Path to the Tesseract OCR executable (change it to your specific installation path)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Function to extract text from an image using PyTesseract OCR
def enhance_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lab_planes = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    lab_planes = list(lab_planes)
    lab_planes[0] = clahe.apply(lab_planes[0])
    lab = cv2.merge(lab_planes)
    enhanced_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return enhanced_image

def extract_text_from_image(image):
    enhanced_image = enhance_contrast(image)
    gray = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text.strip()

def process_image_result(initial_url, final_url, taskId, userId, type):
    if type == 'post-like':
        process_post_like(initial_url, final_url, taskId, userId)
    elif type == 'reel-like':
        process_reel_like(initial_url, final_url, taskId, userId)
    elif type == 'follow':
        process_follow_status(initial_url, final_url, taskId, userId)
    else:
        return

    # Remove the processed image URLs from the queue
    image_queue.task_done()

    # Check if there are more images in the queue
    if not image_queue.empty():
        # Get the next image URLs from the queue
        next_image_urls = image_queue.get()
        # Ensure next_image_urls is a dictionary-like object
        if isinstance(next_image_urls, dict):
            # Extract the URLs
            next_initial_url = next_image_urls.get('initial_url')
            next_final_url = next_image_urls.get('final_url')
            next_taskId = next_image_urls.get('taskId')
            next_userId = next_image_urls.get('userId')
            next_type = next_image_urls.get('type')

            # Process the next image in the queue
            process_image_result(next_initial_url, next_final_url, next_taskId, next_userId, next_type)
    else:
        # All images have been processed
        response_data = jsonify(
            {
            "result":"All images processed"
            }
        )

        print(response_data.get_json()) 

        # # Send the response_data to the specified URL
        # url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        # response = requests.post(url, json=response_data.get_json())
        # print(response.json())  # Print the response from the URL
        # Convert response_data to a JSON string
        response_payload = json.dumps(response_data.get_json())
        headers = {'Content-Type': 'application/json'}

        # Send the response_payload as the payload to the specified URL
        url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        response = requests.post(url, data=response_payload, headers=headers)
        print(response.json())  # Print the response from the URL


# Function to process the image result
def  process_post_like(initial_url, final_url, taskId, userId):
    with app.app_context():
        try:
            initial_image = urllib.request.urlopen(initial_url)
            final_image = urllib.request.urlopen(final_url)
            initial_np_arr = np.asarray(bytearray(initial_image.read()), dtype=np.uint8)
            final_np_arr = np.asarray(bytearray(final_image.read()), dtype=np.uint8)
            initial_screenshot = cv2.imdecode(initial_np_arr, cv2.IMREAD_COLOR)
            final_screenshot = cv2.imdecode(final_np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({'status': 'fail', 'code': 500, 'message': str(e)}), 500

        # Set the region of interest (ROI) coordinates for the like count as a percentage of the screen size
        roi_x = 0  # Convert to percentage
        roi_y = 0  # Convert to percentage
        roi_width = initial_screenshot.shape[1]  # Convert to percentage
        roi_height = initial_screenshot.shape[0]  # Convert to percentage

        # Set the region of interest (ROI) for the like count in the initial and final screenshots
        initial_roi = initial_screenshot[int(roi_y * initial_screenshot.shape[0] / 100):int((roi_y + roi_height) * initial_screenshot.shape[0] / 100),
                                        int(roi_x * initial_screenshot.shape[1] / 100):int((roi_x + roi_width) * initial_screenshot.shape[1] / 100)]
        final_roi = final_screenshot[int(roi_y * final_screenshot.shape[0] / 100):int((roi_y + roi_height) * final_screenshot.shape[0] / 100),
                                    int(roi_x * final_screenshot.shape[1] / 100):int((roi_x + roi_width) * final_screenshot.shape[1] / 100)]

        initial_red_pixels = np.sum(initial_roi[:, :, 2] > 0)
        final_red_pixels = np.sum(final_roi[:, :, 2] > 0)

        if final_red_pixels > initial_red_pixels:
            result = "User liked the post!"
            user_liked = 1
        elif final_red_pixels < initial_red_pixels:
            result = "User unliked the post."
            user_liked = 0
        else:
            result = "No change in like status."
            user_liked = 0

        # response_data = jsonify({'status': 'success', 'code': 200, 'message': result, 'data': {'result': user_liked, 'taskId': taskId, 'userId': userId}})

        response_data = jsonify(
            {
            "taskId": taskId,
            "userId": userId,
            "result": user_liked
            }
        )

        print(response_data.get_json()) 

        # # Send the response_data to the specified URL
        # url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        # response = requests.post(url, json=response_data.get_json())
        # print(response.json())  # Print the response from the URL
        # Convert response_data to a JSON string
        response_payload = json.dumps(response_data.get_json())
        headers = {'Content-Type': 'application/json'}

        # Send the response_payload as the payload to the specified URL
        url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        response = requests.post(url, data=response_payload, headers=headers)
        print(response.json())  # Print the response from the URL

        



def  process_reel_like(initial_url, final_url, taskId, userId):
    with app.app_context():
        try:
            initial_image = urllib.request.urlopen(initial_url)
            final_image = urllib.request.urlopen(final_url)
            initial_np_arr = np.asarray(bytearray(initial_image.read()), dtype=np.uint8)
            final_np_arr = np.asarray(bytearray(final_image.read()), dtype=np.uint8)
            initial_screenshot = cv2.imdecode(initial_np_arr, cv2.IMREAD_COLOR)
            final_screenshot = cv2.imdecode(final_np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({'status': 'fail', 'code': 500, 'message': str(e)}), 500

        # Set the region of interest (ROI) coordinates for the like count as a percentage of the screen size
        roi_x = 0  # Convert to percentage
        roi_y = 75  # Convert to percentage
        roi_width = initial_screenshot.shape[1]  # Convert to percentage
        roi_height =10 # Convert to percentage

        # Set the region of interest (ROI) for the like count in the initial and final screenshots
        initial_roi = initial_screenshot[int(roi_y * initial_screenshot.shape[0] / 100):int((roi_y + roi_height) * initial_screenshot.shape[0] / 100),
                                        int(roi_x * initial_screenshot.shape[1] / 100):int((roi_x + roi_width) * initial_screenshot.shape[1] / 100)]
        final_roi = final_screenshot[int(roi_y * final_screenshot.shape[0] / 100):int((roi_y + roi_height) * final_screenshot.shape[0] / 100),
                                    int(roi_x * final_screenshot.shape[1] / 100):int((roi_x + roi_width) * final_screenshot.shape[1] / 100)]

        initial_red_pixels = np.sum(initial_roi[:, :, 2] > 0)
        final_red_pixels = np.sum(final_roi[:, :, 2] > 0)

        if final_red_pixels > initial_red_pixels:
            result = "User liked the post!"
            user_liked = 1
        elif final_red_pixels < initial_red_pixels:
            result = "User unliked the post."
            user_liked = 0
        else:
            result = "No change in like status."
            user_liked = 0

        # response_data = jsonify({'status': 'success', 'code': 200, 'message': result, 'data': {'result': user_liked, 'taskId': taskId, 'userId': userId}})

        response_data = jsonify(
            {
            "taskId": taskId,
            "userId": userId,
            "result": user_liked
            }
        )

        print(response_data.get_json()) 

        # # Send the response_data to the specified URL
        # url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        # response = requests.post(url, json=response_data.get_json())
        # print(response.json())  # Print the response from the URL
        # Convert response_data to a JSON string
        response_payload = json.dumps(response_data.get_json())
        headers = {'Content-Type': 'application/json'}

        # Send the response_payload as the payload to the specified URL
        url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        response = requests.post(url, data=response_payload, headers=headers)
        print(response.json())  # Print the response from the URL



# def process_comment_status(initial_url, final_url, taskId, userId):
#     with app.app_context():
#         try:
#             initial_image_response = requests.get(initial_url)
#             initial_image_np_arr = np.asarray(bytearray(initial_image_response.content), dtype=np.uint8)
#             initial_image = cv2.imdecode(initial_image_np_arr, cv2.IMREAD_COLOR)

#             final_image_response = requests.get(final_url)
#             final_image_np_arr = np.asarray(bytearray(final_image_response.content), dtype=np.uint8)
#             final_image = cv2.imdecode(final_image_np_arr, cv2.IMREAD_COLOR)
#         except Exception as e:
#             return jsonify({'status': 'fail', 'code': 500, 'message': str(e)}), 500
        
#         # Set the region of interest (ROI) coordinates for the comment text as a percentage of the image size
#         roi_x = 0  # Convert to percentage
#         roi_y = 75  # Convert to percentage
#         roi_width = initial_image.shape[1]  # Convert to percentage
#         roi_height = 10  # Convert to percentage

#         # Set the region of interest (ROI) for the comment text in the initial and final images
#         initial_roi = initial_image[int(roi_y * initial_image.shape[0] / 100):int((roi_y + roi_height) * initial_image.shape[0] / 100),
#                                     int(roi_x * initial_image.shape[1] / 100):int((roi_x + roi_width) * initial_image.shape[1] / 100)]

#         final_roi = final_image[int(roi_y * final_image.shape[0] / 100):int((roi_y + roi_height) * final_image.shape[0] / 100),
#                                 int(roi_x * final_image.shape[1] / 100):int((roi_x + roi_width) * final_image.shape[1] / 100)]

#         initial_comment_text = extract_text_from_image(initial_roi)
#         final_comment_text = extract_text_from_image(final_roi)

#         if len(initial_comment_text) > 0 or len(final_comment_text) > 0:
#             result = "User commented"
#             user_commented = 1
#         else:
#             result = "No comment"
#             user_commented = 0

#         response_data = jsonify({
#             "taskId": taskId,
#             "userId": userId,
#             "result": user_commented
#         })

#         print(response_data.get_json()) 

#         # # Send the response_data to the specified URL
#         # url = 'https://project-b-olive.vercel.app/api/ml/get-result'
#         # response = requests.post(url, json=response_data.get_json())
#         # print(response.json())  # Print the response from the URL
#         # Convert response_data to a JSON string
#         response_payload = json.dumps(response_data.get_json())
#         headers = {'Content-Type': 'application/json'}

#         # Send the response_payload as the payload to the specified URL
#         url = 'https://project-b-olive.vercel.app/api/ml/get-result'
#         response = requests.post(url, data=response_payload, headers=headers)
#         print(response.json())  # Print the response from the URL

#     image_queue.task_done()

def process_follow_status(initial_url, final_url, taskId, userId):
    with app.app_context():
        try:
            initial_image_response = requests.get(initial_url)
            initial_image_np_arr = np.asarray(bytearray(initial_image_response.content), dtype=np.uint8)
            initial_image = cv2.imdecode(initial_image_np_arr, cv2.IMREAD_COLOR)

            final_image_response = requests.get(final_url)
            final_image_np_arr = np.asarray(bytearray(final_image_response.content), dtype=np.uint8)
            final_image = cv2.imdecode(final_image_np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({'status': 'fail', 'code': 500, 'message': str(e)}), 500
        height, width, _ = initial_image.shape
        # Set the region of interest (ROI) coordinates for the follow button as a percentage of the screen size
        roi_x = 0  # Convert to percentage
        roi_y = 0  # Convert to percentage
        roi_width = width  # Convert to percentage
        roi_height =30  # Convert to percentage

            # Set the region of interest (ROI) for the follow button in the initial and final screenshots
        initial_roi = initial_image[int(roi_y * height / 100):int((roi_y + roi_height) * height / 100),
                                             int(roi_x * width / 100):int((roi_x + roi_width) * width / 100)]
        final_roi = final_image[int(roi_y * height / 100):int((roi_y + roi_height) * height / 100),
                                         int(roi_x * width / 100):int((roi_x + roi_width) * width / 100)]

        # Apply OCR to extract text from the region of interest in the initial and final screenshots
        initial_text = extract_text_from_image(initial_roi)
        final_text = extract_text_from_image(final_roi)
       
       

        # Process the extracted text to consider only the following text
        # initial_text = initial_text.split("Following", 1)[-1].strip()
        # final_text = final_text.split("Following", 1)[-1].strip()

            # Check if the follow button text has changed from the initial to the final screenshot
        result = ""
        if "Follow" in initial_text and "Following" in final_text and "Following" not in initial_text:
            result = "User followed on Instagram!"
            user_followed = 1
        elif "Following" in initial_text and "Follow" in final_text and "Following" not in final_text:
            result = "User unfollowed on Instagram!"
            user_followed = 0
        else:
            result = "No change in follow status."
            user_followed = 0

        response_data = jsonify({
            "taskId": taskId,
            "userId": userId,
            "result": user_followed
        })

        print(response_data.get_json()) 

        # # Send the response_data to the specified URL
        # url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        # response = requests.post(url, json=response_data.get_json())
        # print(response.json())  # Print the response from the URL
        # Convert response_data to a JSON string
        response_payload = json.dumps(response_data.get_json())
        headers = {'Content-Type': 'application/json'}

        # Send the response_payload as the payload to the specified URL
        url = 'https://project-b-olive.vercel.app/api/ml/get-result'
        response = requests.post(url, data=response_payload, headers=headers)
        print(response.json())  # Print the response from the URL




@app.route('/receive-image', methods=['POST'])
def receive_image():
    initial_url = request.json['initial_url']
    final_url = request.json['final_url']
    taskId = request.json['taskId']
    userId = request.json['userId']
    type = request.json['type']

    # Add the image URLs and task_id to the queue
    image_queue.put((initial_url, final_url, taskId, userId, type))

    process_thread = Thread(target=process_image_result, args=(initial_url, final_url, taskId, userId, type))
    process_thread.start()
    

    return jsonify({'status': 'success', 'code': 200, 'message': 'Images received',
                    'data': {'received': 1, 'queue_position': image_queue.qsize(), 'task_id': taskId, 'userId': userId}}), 200


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'status': 'error', 'code': 404, 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'status': 'fail', 'code': 500, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
