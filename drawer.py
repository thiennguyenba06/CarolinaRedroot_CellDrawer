from flask import Flask, request, send_file
import io, os, pyexiv2, numpy as np, cv2, time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

app = Flask(__name__)

# Constants -- subject to change
SENSOR_FOV_VERTICAL = np.radians(55.072)
SENSOR_FOV_HORIZONTAL = np.radians(69.72)
SIDE_LENGTH = 1

IMG_FOLDER_ID = "14si2OAqbEPs0iRJf2RiXhCEZzee8f3Uu"
ANNOTATED_IMG_FOLDER_ID = "1jgVc4-6nfvCi7RMvkbYIy089Xci0nuGb"
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Initialize Drive Service
creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def fetch_from_drive(file_name, folder_id, metadata_boolean):
    # Find the file in the specific folder
    query = f"name = '{file_name}' and '{folder_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])
    
    if not items:
        return None
    
    # Stream the file content into a memory buffer
    file_id = items[0]['id']
    if metadata_boolean is True:
        request = drive_service.files().get_media(fileId=file_id)
        request.headers['Range'] = 'bytes=0-200000' 
    else:
        request = drive_service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    return fh.getvalue()


def inversed_georef(x_dist, y_dist, drone_height, pitch, img_width, img_height):
    SO = img_height / (2 * np.tan(SENSOR_FOV_VERTICAL / 2))
    SO_x = img_width / (2 * np.tan(SENSOR_FOV_HORIZONTAL / 2)) 
    y = np.tan(np.arctan(y_dist / drone_height) - (np.pi/2 + pitch)) * SO
    x = x_dist * np.sqrt(SO_x**2 + y**2) / np.sqrt(drone_height**2 + y_dist**2)
    # shift coor of x,y from center origin to top left origin
    x = x + (img_width / 2)
    y = (img_height / 2) - y

    return int(x), int(y)


@app.route('/render')
def render_box():
    # Parameters sent from QGIS Map Tip
    img_name = request.args.get('img')
    local_x = float(request.args.get('x')) 
    local_y = float(request.args.get('y'))


    # fetch from drive to extract metadata
    file_bytes = fetch_from_drive(img_name, IMG_FOLDER_ID, True)
    if not file_bytes:
        return f"image {img_name} not found for metadata extraction", 404

    # extract metadata from RAM
    try:
        with pyexiv2.ImageData(file_bytes) as meta:
            xmp = meta.read_xmp()
            exif = meta.read_exif()
            
            pitch = np.radians(float(xmp.get('Xmp.drone-dji.GimbalPitchDegree', 0)))
            altitude = float(xmp.get('Xmp.drone-dji.RelativeAltitude', 10)) + 1
            width = float(exif.get('Exif.Photo.PixelXDimension'))
            height = float(exif.get('Exif.Photo.PixelYDimension'))
            print(f"drone_alt: {altitude} img_heigh: {height} img_width: {width}")
            print(f"pitch for img: {np.degrees(pitch)}")
    except Exception as e:
        return f"Could not extract metadata from {img_name} from Drive: {e}", 500

    # read annotated image
    file_bytes = fetch_from_drive(img_name, ANNOTATED_IMG_FOLDER_ID, False)
    if not file_bytes:
        return f"image {img_name} not found in output folder.", 404
    
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Calculate the 4 corners of cell on image
    top_left = inversed_georef(local_x - SIDE_LENGTH / 2, local_y + SIDE_LENGTH / 2, altitude, pitch, width, height)
    top_right = inversed_georef(local_x + SIDE_LENGTH / 2, local_y + SIDE_LENGTH / 2, altitude, pitch, width, height)
    bottom_right = inversed_georef(local_x + SIDE_LENGTH / 2, local_y - SIDE_LENGTH / 2, altitude, pitch, width, height)
    bottom_left = inversed_georef(local_x - SIDE_LENGTH / 2, local_y - SIDE_LENGTH / 2, altitude, pitch, width, height)

    # Draw  cell
    print([top_left, top_right, bottom_right, bottom_left])
    pts = np.int32([top_left, top_right, bottom_right, bottom_left])
    cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=13)
    
    # Convert to JPEG for the web browser/QGIS
    _, buffer = cv2.imencode('.jpg', img)
    print("\n")
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded = False)