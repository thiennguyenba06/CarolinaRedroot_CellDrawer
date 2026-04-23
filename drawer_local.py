from flask import Flask, request, send_file
import io, os, pyexiv2, numpy as np, cv2, time

app = Flask(__name__)

# Constants -- subject to change
IMG_DIR = "/app/geotagged_images"
SENSOR_FOV_VERTICAL = np.radians(55.072)
SENSOR_FOV_HORIZONTAL = np.radians(69.72)
SIDE_LENGTH = 1




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

    img_path = os.path.join(IMG_DIR, img_name)
    
    if not os.path.exists(img_path):
        return "Image not found", 404

    # Extract metadata from image
    with pyexiv2.Image(img_path) as meta:
        xmp = meta.read_xmp()
        exif = meta.read_exif()
        
        # Get pitch and altitude
        pitch = np.radians(float(xmp.get('Xmp.drone-dji.GimbalPitchDegree', 0)))
        altitude = float(xmp.get('Xmp.drone-dji.RelativeAltitude', 10)) + 1
        yaw = np.radians(90 - float(xmp.get('Xmp.drone-dji.FlightYawDegree')))
        
        width = float(exif.get('Exif.Photo.PixelXDimension'))
        height = float(exif.get('Exif.Photo.PixelYDimension'))



    # meta_success = False
    # max_retries = 10
    # for attempt in range(max_retries):
    #     try:
    #         if not os.path.exists(img_path):
    #             raise FileNotFoundError(f"File not found on drive yet: {img_path}")
                
    #         with pyexiv2.Image(img_path) as meta:
    #             xmp = meta.read_xmp()
    #             exif = meta.read_exif()
                
    #             pitch = np.radians(float(xmp.get('Xmp.drone-dji.GimbalPitchDegree', 0)))
    #             altitude = float(xmp.get('Xmp.drone-dji.RelativeAltitude', 10)) + 1
    #             width = float(exif.get('Exif.Photo.PixelXDimension'))
    #             height = float(exif.get('Exif.Photo.PixelYDimension'))
    #             meta_success = True
    #             break # Exit loop if successful
    #     except (RuntimeError, FileNotFoundError, Exception) as e:
    #         print(f"Attempt {attempt + 1} failed for {img_name}: {e}")
    #         time.sleep(1.5) # Wait for Drive to sync the file bits
            
    # if not meta_success:
    #     return f"Error: Could not read metadata for {img_name} after {max_retries} attempts.", 500

    # Read image 
    img = cv2.imread('/app/annotated_images/' + img_name)
    # img = None
    # for attempt in range(max_retries):
    #     img = cv2.imread(img_path)
    #     if img is not None:
    #         break
    #     print(f"Image bits not ready for {img_name}, retrying...")
    #     time.sleep(2) # Give Drive more time to stream the actual pixel data

    # if img is None:
    #     return f"Image data empty for {img_name} after retries", 404
    
    # Calculate the 4 corners of cell on image
    top_left = inversed_georef(local_x - SIDE_LENGTH / 2, local_y + SIDE_LENGTH / 2, altitude, pitch, width, height)
    top_right = inversed_georef(local_x + SIDE_LENGTH / 2, local_y + SIDE_LENGTH / 2, altitude, pitch, width, height)
    bottom_right = inversed_georef(local_x + SIDE_LENGTH / 2, local_y - SIDE_LENGTH / 2, altitude, pitch, width, height)
    bottom_left = inversed_georef(local_x - SIDE_LENGTH / 2, local_y - SIDE_LENGTH / 2, altitude, pitch, width, height)

    # Draw  cell
    print(f"drone_alt: {altitude} img_heigh: {height} img_width: {width}")
    print([top_left, top_right, bottom_right, bottom_left])
    print(f"pitch for img: {pitch}")
    pts = np.int32([top_left, top_right, bottom_right, bottom_left])
    cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=13)
    
    # Convert to JPEG for the web browser/QGIS
    _, buffer = cv2.imencode('.jpg', img)
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)