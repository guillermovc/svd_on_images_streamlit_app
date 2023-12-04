import contextlib
import requests
from PIL import Image
from io import BytesIO

import numpy as np
import plotly.express as px
import streamlit as st
from sklearn.decomposition import TruncatedSVD


# Function to perform SVD and reconstruct the image
def svd_and_reconstruct(image, svd):
    # Convert the image to a NumPy array
    image_array = np.array(image)

    # Convert colored image to grayscale
    if len(image_array.shape) == 3:
        image_array = np.mean(image_array, axis=-1)

    # Apply TruncatedSVD
    image_reconstructed = svd.fit_transform(image_array)
    image_reconstructed = np.dot(image_reconstructed, svd.components_)

    # Normalize the reconstructed image to [0, 255]
    image_reconstructed -= np.min(image_reconstructed)
    image_reconstructed /= np.max(image_reconstructed)
    image_reconstructed *= 255

    return image_reconstructed.astype(np.uint8)

# Function to plot the cumulative variance explained
def plot_cumulative_variance(svd, max_components):
    explained_variance_ratio = np.cumsum(svd.explained_variance_ratio_)
    fig = px.line(x=range(1, max_components + 1), y=explained_variance_ratio, markers=True)
    fig.update_layout(title='Cumulative Variance Explained', 
                      xaxis_title='Number of Components', 
                      yaxis_title='Cumulative Variance Explained')
    st.plotly_chart(fig)


st.set_page_config(
    page_title="SVD on images",
    page_icon="🖼️",
)

st.markdown("""
# Singular Value Decomposition on Images
            """)

option = st.radio(
    label="Upload an image, take one with your camera, or load image from a URL",
    options=(
        "Upload an image ⬆️",
        "Take a photo with my camera 📷",
        "Load image from a URL 🌐",
    ),
    help="Uploaded images are deleted from the server when you\n* upload another image\n* clear the file uploader\n* close the browser tab",
)

if option == "Take a photo with my camera 📷":
    upload_img = st.camera_input(
        label="Take a picture",
    )
    mode = "camera"

elif option == "Upload an image ⬆️":
    upload_img = st.file_uploader(
        label="Upload an image",
        type=["bmp", "jpg", "jpeg", "png", "svg"],
    )
    mode = "upload"

elif option == "Load image from a URL 🌐":
    url = st.text_input(
        "Image URL",
        key="url",
    )
    mode = "url"

    if url != "":
        try:
            response = requests.get(url)
            upload_img = Image.open(BytesIO(response.content))
        except:
            st.error("The URL does not seem to be valid.")

with contextlib.suppress(NameError):
    cols = st.columns(2)
    if upload_img is not None:
        pil_img = (
            upload_img.convert("RGB")
            if mode == "url"
            else Image.open(upload_img).convert("RGB")
        )
        pil_img = pil_img.convert("L")
        img_arr = np.asarray(pil_img)

        
        h, w = img_arr.shape[:2]
        print(img_arr.shape)

        cols[0].image(img_arr, use_column_width="auto", caption="Uploaded Image")
        st.text(
            f"Original width = {pil_img.size[0]}px and height = {pil_img.size[1]}px"
        )

        st.caption("All changes are applied on top of the previous change.")


    # SVD Decomposition
    k = st.slider(label="Number of components", min_value=1, max_value=h, value=10, step=2)
    svd = TruncatedSVD(n_components=k)
    reconstructed_image = svd_and_reconstruct(img_arr, svd)

    cols[1].image(reconstructed_image, clamp=[0,1.0])

    st.subheader("Cumulative Variance")
    plot_cumulative_variance(svd, k)