
import streamlit as st
from rapidocr import RapidOCR
from PIL import Image
import tempfile
import os
import re

st.set_page_config(
    page_title="My Cat's Choice",
    page_icon="🐱",
    layout="wide"
)

@st.cache_resource
def load_ocr():
    return RapidOCR()

def extract_text(image):
    engine = load_ocr()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
        image.convert("RGB").save(temp.name, format="JPEG")
        image_path = temp.name

    try:
        result = engine(image_path)
        texts = result.txts or []
        return [str(text).strip() for text in texts if text and str(text).strip()]
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

def detect_category(text):
    text = text.lower()

    categories = {
        "Food & Beverages": [
            "ingredients", "nutrition", "calories", "protein",
            "carbohydrate", "fat", "sugar", "food", "flavour",
            "flavor", "serving", "vitamin"
        ],
        "Cosmetics & Personal Care": [
            "skin", "hair", "cream", "shampoo", "conditioner",
            "moisturizer", "moisturiser", "serum", "spf"
        ],
        "Electronics": [
            "battery", "voltage", "watt", "wireless", "bluetooth",
            "usb", "charger", "electronic"
        ],
        "Clothing & Fashion": [
            "cotton", "polyester", "fabric", "size", "wash",
            "material", "textile"
        ],
        "Household Products": [
            "detergent", "cleaner", "disinfectant", "washing",
            "cleaning", "household"
        ]
    }

    scores = {
        category: sum(1 for word in keywords if word in text)
        for category, keywords in categories.items()
    }

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "General Consumer Product"

    return best_category

def price_per_unit(price, quantity):
    if price is None or quantity is None or quantity <= 0:
        return None
    return price / quantity

def compare_products(text_a, text_b, preferences):
    words_a = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_a.lower()))
    words_b = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_b.lower()))

    shared = words_a & words_b
    unique_a = words_a - words_b
    unique_b = words_b - words_a

    preference_matches_a = [
        word for word in preferences if word.lower() in text_a.lower()
    ]
    preference_matches_b = [
        word for word in preferences if word.lower() in text_b.lower()
    ]

    return shared, unique_a, unique_b, preference_matches_a, preference_matches_b

st.title("🐱 My Cat's Choice")
st.subheader("Compare products and make a more informed choice.")
st.write("Upload two product photos to compare their packaging information, prices and your preferences.")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### Product A")
    image_a = st.file_uploader(
        "Upload Product A photo",
        type=["jpg", "jpeg", "png"],
        key="product_a"
    )
    price_a = st.number_input(
        "Price of Product A",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="price_a"
    )
    quantity_a = st.number_input(
        "Quantity of Product A",
        min_value=0.0,
        value=1.0,
        step=1.0,
        key="quantity_a"
    )

with col_b:
    st.markdown("### Product B")
    image_b = st.file_uploader(
        "Upload Product B photo",
        type=["jpg", "jpeg", "png"],
        key="product_b"
    )
    price_b = st.number_input(
        "Price of Product B",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="price_b"
    )
    quantity_b = st.number_input(
        "Quantity of Product B",
        min_value=0.0,
        value=1.0,
        step=1.0,
        key="quantity_b"
    )

st.divider()

st.markdown("### Your preferences")
preferences_input = st.text_input(
    "What matters to you?",
    placeholder="For example: low sugar, organic, cotton, fragrance-free"
)

preferences = [
    item.strip()
    for item in preferences_input.split(",")
    if item.strip()
]

if st.button("Compare Products", type="primary", use_container_width=True):

    if image_a is None or image_b is None:
        st.error("Please upload photos of both products.")
    else:
        try:
            with st.spinner("Reading product information and comparing..."):
                pil_a = Image.open(image_a)
                pil_b = Image.open(image_b)

                text_a = extract_text(pil_a)
                text_b = extract_text(pil_b)

                full_text_a = " ".join(text_a)
                full_text_b = " ".join(text_b)

                category_a = detect_category(full_text_a)
                category_b = detect_category(full_text_b)

                shared, unique_a, unique_b, matches_a, matches_b = (
                    compare_products(full_text_a, full_text_b, preferences)
                )

                unit_price_a = price_per_unit(price_a, quantity_a)
                unit_price_b = price_per_unit(price_b, quantity_b)

            st.success("Comparison completed!")

            result_a, result_b = st.columns(2)

            with result_a:
                st.markdown("### Product A")
                st.image(pil_a, use_container_width=True)
                st.write("**Detected category:**", category_a)
                st.write("**Price:**", f"{price_a:.2f}")
                st.write("**Quantity:**", quantity_a)
                if unit_price_a is not None:
                    st.write("**Price per unit:**", f"{unit_price_a:.2f}")
                st.write("**Preference matches:**",
                         ", ".join(matches_a) if matches_a else "No matches found")

            with result_b:
                st.markdown("### Product B")
                st.image(pil_b, use_container_width=True)
                st.write("**Detected category:**", category_b)
                st.write("**Price:**", f"{price_b:.2f}")
                st.write("**Quantity:**", quantity_b)
                if unit_price_b is not None:
                    st.write("**Price per unit:**", f"{unit_price_b:.2f}")
                st.write("**Preference matches:**",
                         ", ".join(matches_b) if matches_b else "No matches found")

            st.divider()
            st.markdown("### Comparison results")

            if category_a == category_b:
                st.write("Both products appear to belong to:", category_a)
            else:
                st.write(
                    f"Product categories differ: {category_a} and {category_b}. "
                    "Check the packaging information carefully."
                )

            if unit_price_a is not None and unit_price_b is not None:
                if unit_price_a < unit_price_b:
                    st.info("Product A has the lower price per unit.")
                elif unit_price_b < unit_price_a:
                    st.info("Product B has the lower price per unit.")
                else:
                    st.info("Both products have the same price per unit.")

            if preferences:
                st.markdown("**Your preference comparison**")
                st.write("Product A matches:", ", ".join(matches_a) if matches_a else "None detected")
                st.write("Product B matches:", ", ".join(matches_b) if matches_b else "None detected")

            with st.expander("View extracted packaging text"):
                st.markdown("**Product A text**")
                st.write("\n".join(text_a) if text_a else "No text detected.")
                st.markdown("**Product B text**")
                st.write("\n".join(text_b) if text_b else "No text detected.")

            with st.expander("View words found on both products"):
                st.write(", ".join(sorted(shared)) if shared else "No common words detected.")

            st.caption(
                "This comparison is based on text detected from product photos "
                "and the information entered. Always check product labels and "
                "claims yourself before making a purchase."
            )

        except Exception as error:
            st.error(f"Something went wrong: {error}")
            st.info("Please try again with clear, well-lit product photos.")
