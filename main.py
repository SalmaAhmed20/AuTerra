import cv2
import boto3
import json
from utils import extract_resources,Generate_Terraform,extract_code_blocks,create_terraform_message_from_json
from tqdm import tqdm
from colorama import init, Fore, Style
import time
# Initialize colorama
init()

# Define the dash patterns for each character
dash_patterns = {
    'A': ["  A  ", " A-A ", "A---A", "AAAAA", "A---A"],
    'E': ["EEEEE", "E    ", "EEEEE", "E    ", "EEEEE"],
    'L': ["L    ", "L    ", "L    ", "L    ", "LLLLL"],
    'O': [" OOO ", "O   O", "O   O", "O   O", " OOO "],
    'T': ["TTTTT", "  T  ", "  T  ", "  T  ", "  T  "],
    'R': ["RRRR ", "R   R", "RRRR ", "R R  ", "R  RR"],
    'U': ["U   U", "U   U", "U   U", "U   U", " UUU "],
    'W': ["W   W", "W   W", "W W W", "WW WW", "W   W"],
    'C': [" CCCC", "C    ", "C    ", "C    ", " CCCC"],
    'M': ["M   M", "MM MM", "M M M", "M   M", "M   M"],
    ' ': ["     ", "     ", "     ", "     ", "     "],
}
# Define the message
message = "WELCOME TO AUTERRA"

# Convert the message to dash patterns
lines = ["", "", "", "", ""]
for char in message:
    if char in dash_patterns:
        pattern = dash_patterns[char]
        for i in range(5):
            lines[i] += pattern[i] + "  "

# Print the dash patterns in color
for line in lines:
    print(Fore.CYAN + Style.BRIGHT + line)

# Reset colorama
print(Style.RESET_ALL)
#####################################################

# Amazon Textract
textract = boto3.client('textract')
# Video processing
video = cv2.VideoCapture('media/input_video.mp4')
success, prev_frame = video.read()

# Get the total number of frames
total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

# Set the threshold for detecting changes
threshold = 5  # Adjust this value as needed
# Set the frame skip interval (e.g., process every 10th frame)
frame_skip_interval = 60
print(Fore.GREEN + "Extracting Resources and Specifcations .." + Style.RESET_ALL)
pbar = tqdm(total=total_frames, unit='frames')
frame_count = 0
while True:
    success, frame = video.read()
    if not success:
        break
    frame_count += 1

    # Skip frames based on the frame_skip_interval
    if frame_count % frame_skip_interval != 0:
        pbar.update(1)    
        continue
    # Calculate the absolute difference between the current and previous frames
    frame_diff = cv2.absdiff(frame, prev_frame)
    gray_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
    # Check if the difference is above the threshold
    if cv2.countNonZero(gray_diff) > threshold:
        # Save the frame as an image file
        cv2.imwrite('frame.jpg', frame)
        s3 = boto3.client('s3')
        bucket_name = 'test-975050225829'
        file_name = 'frame.jpg'
        s3.upload_file(file_name, bucket_name, file_name)

        response = textract.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': file_name
                }
            },
            NotificationChannel={
                'SNSTopicArn': 'arn:aws:sns:eu-central-1:975050225829:autoterra',
                'RoleArn': 'arn:aws:iam::975050225829:role/autoterra'
            }
        )
    prev_frame = frame
    pbar.update(1)    
video.release()
pbar.close()
job_id = response['JobId']

# Wait for the job to complete
while True:
    result = textract.get_document_text_detection(JobId=job_id)
    status = result['JobStatus']
    if status in ('SUCCEEDED', 'FAILED', 'PARTIAL'):
        break

if status == 'SUCCEEDED':
    text = ''
    for block in result['Blocks']:
        if 'Text' in block:
            text += block['Text'] + ' '
    # NLP processing
    resources = extract_resources(text)
    # JSON generation
    with open('resources.json', 'w') as f:
        json.dump(resources, f)
    message = f"""
        Create a Terraform configuration to deploy this resources {list(resources.keys())} following specifications:
        {resources.values()}
        """
    message = create_terraform_message_from_json('media/resources.json')
    # print(message)
        # Define the total number of iterations
    total_iterations = 100

    # Create a progress bar
    print(Fore.GREEN + "Terraform Code Coming" + Style.RESET_ALL)
    for i in tqdm(range(total_iterations)):
        # Simulate some work with a sleep
        time.sleep(0.1)        
    response = Generate_Terraform(message)
    with open('resources.tf', 'w') as f:
        f.write(extract_code_blocks(response))
    print(Fore.GREEN + "Your Terraform configuration has been saved at " + Fore.YELLOW + 'resources.tf' + Style.RESET_ALL)
else:
    print(f"Error: {result}")
