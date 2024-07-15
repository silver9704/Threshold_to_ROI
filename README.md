# Threshold to ROI - QGIS Plugin

![icon](icon/icon.png)

Threshold to ROI is a QGIS plugin that helps you create a Region of Interest (ROI) using threshold values selected from the histogram of a raster layer. This plugin is useful for extracting specific areas from raster data based on user-defined threshold values.

## Features

- **User-friendly Interface**: An easy and intuitive user interface for selecting threshold values and creating ROIs.
- **Real-time Preview**: Allows users to preview the results in real-time before applying the changes.
- **Error Handling**: Provides error handling for invalid input and output parameters to ensure smooth operation.

## Usage

1. Load a raster layer into QGIS.
2. Click on the Threshold to ROI button in the toolbar.
3. In the plugin dialog, select the raster layer and the desired band.

![load](https://drive.google.com/uc?export=view&id=1wKWCTEmNI5gMvZXEwqvRQzMNlzlmM9Z3)

4. You can select a color that will be used for the output layer settings.

![color](https://drive.google.com/uc?export=view&id=1XdehElXP7lnZ4tajW9WQQoJPYJQC0y5E)

5. Use the histogram to set the minimum and maximum threshold values. Click on the "histogram" button and a window with the histogram of the raster layer will open.

![histogram](https://drive.google.com/uc?export=view&id=1SWYyWY6zpuoKXzntUT1Owm3-lnFj8DXt)

6. Use the color span to select the range of threshold values. If you want to see a preview of the ROI, click on the "Preview" checkbox, a preview layer will load and update in real time when you move the color span.

https://github.com/user-attachments/assets/cd41ef8e-d5a9-4153-a9c2-e64b40e6fe6f

7. Select the path for the output raster layer.

![output_path](https://drive.google.com/uc?export=view&id=1zPob5iUAknEEbrqAFifC2yEYz4grZXqH)

8. Finally click accept to create the ROI raster layer. This layer will be automatically loaded into the project.

![result](https://drive.google.com/uc?export=view&id=1CoEWsYLtMAIngZcqubu8z-2y2mJB8Ibb)

## License

This plugin is licensed under the GNU General Public License v3.0.

## Contribution

Contributions are welcome! Please visit the GitHub Repository to report issues or suggest features.

## Support

For support and further information, please contact Silver Piedra at silverpiedraherrera@gmail.com