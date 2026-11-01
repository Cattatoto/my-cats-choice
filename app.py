import os
os.environ["FLAGS_use_mkldnn"] = "0"

import re
import tempfile
import streamlit as st
from paddleocr import PaddleOCR

# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="My Cat's Choice",
    page_icon="🛍️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #F8F5FC;
}
.product-a {
    background-color: #FFF0F5;
    padding: 18px;
    border-radius: 18px;
}
.product-b {
    background-color: #EEF5FF;
    padding: 18px;
    border-radius: 18px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛍️ My Cat's Choice")
st.subheader("Find the product that best matches your needs")
st.write(
    "Compare food, cosmetics, electronics, clothing "
    "and household products."
)

# =====================================
# INITIALISE OCR
# =====================================

@st.cache_resource
def load_ocr():
    return PaddleOCR(
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False
    )

# =====================================
# PRODUCT ANALYSIS
# =====================================

def analyse_product(uploaded_file, price, quantity, label):

    if uploaded_file is None:
        return None, f"Please upload a photo for {label}."

    try:
        suffix = os.path.splitext(uploaded_file.name)[1] or ".jpg"

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as temp:
            temp.write(uploaded_file.getvalue())
            image_path = temp.name

        try:
            ocr = load_ocr()
            results = ocr.predict(image_path)

            texts = []

            for page in results:
                data = page.json["res"]

                for text in data["rec_texts"]:
                    if text.strip():
                        texts.append(text.strip())

        finally:
            os.remove(image_path)

        if not texts:
            return None, "No readable text detected. Try a clearer photo."

        full_text = " ".join(texts)

        categories = {
            "Food & Beverage": [
                "ingredients", "nutrition", "calories", "protein"
            ],
            "Cosmetics": [
                "skin", "cream", "shampoo", "serum", "moisturizer"
            ],
            "Electronics": [
                "battery", "voltage", "watt", "memory", "bluetooth"
            ],
            "Clothing": [
                "cotton", "polyester", "fabric", "size", "wash"
            ],
            "Household": [
                "detergent", "cleaner", "disinfectant", "washing"
            ]
        }

        detected_category = "General consumer product"

        for category, keywords in categories.items():
            if any(word in full_text.lower() for word in keywords):
                detected_category = category
                break

        price_text = (
            str(price).strip()
            if price is not None and str(price).strip()
            else "Not provided"
        )

        quantity_text = (
            str(quantity).strip()
            if quantity is not None and str(quantity).strip()
            else "Not provided"
        )

        summary = f"### {label}\n\n"
        summary += f"**Category:** {detected_category}\n\n"
        summary += f"**Price:** {price_text}\n\n"
        summary += f"**Quantity / Size:** {quantity_text}\n\n"
        summary += "#### Detected product information\n"

        for text in texts[:15]:
            summary += f"\n- {text}"

        return {
            "category": detected_category,
            "price": price_text,
            "quantity": quantity_text,
            "texts": texts,
            "full_text": full_text
        }, summary

    except Exception as e:
        return None, f"OCR processing error: {str(e)}"


# =====================================
# PRODUCT COMPARISON
# =====================================

def compare_products(a, b, preferences):

    data_a, summary_a = analyse_product(
        a["image"], a["price"], a["quantity"], "Product A"
    )

    data_b, summary_b = analyse_product(
        b["image"], b["price"], b["quantity"], "Product B"
    )

    if data_a is None or data_b is None:
        return summary_a, summary_b, (
            "Please upload readable photos for both products."
        )

    result = "## 🏆 Product Comparison\n\n"

    result += f"""
| Feature | Product A | Product B |
|---|---|---|
| Category | {data_a['category']} | {data_b['category']} |
| Price | {data_a['price']} | {data_b['price']} |
| Quantity | {data_a['quantity']} | {data_b['quantity']} |
| Text detected | {len(data_a['texts'])} lines | {len(data_b['texts'])} lines |
"""

    try:
        pa = float(data_a["price"])
        pb = float(data_b["price"])

        result += "\n### Price observation\n\n"

        if pa < pb:
            result += "Product A has the lower entered price."
        elif pb < pa:
            result += "Product B has the lower entered price."
        else:
            result += "Both products have the same entered price."

    except (ValueError, TypeError):
        result += (
            "\n### Price observation\n\n"
            "Price comparison is unavailable because both prices "
            "must be entered as numbers."
        )

    if preferences and preferences.strip():

        keywords = [
            word.lower()
            for word in re.findall(
                r"\b[a-zA-Z]{4,}\b", preferences
            )
        ]

        score_a = sum(
            word in data_a["full_text"].lower()
            for word in keywords
        )

        score_b = sum(
            word in data_b["full_text"].lower()
            for word in keywords
        )

        result += f"""

### Preference matching

- Product A: {score_a} preference keywords found.
- Product B: {score_b} preference keywords found.
"""

        if score_a > score_b:
            result += "\nProduct A matches more entered keywords."
        elif score_b > score_a:
            result += "\nProduct B matches more entered keywords."
        else:
            result += "\nNeither product has a clear keyword advantage."

    if data_a["category"] != data_b["category"]:
        result += """

### Recommendation

These products appear to belong to different categories.
They should not be ranked directly against each other.
Review each product's detected information and your own needs.
"""
    else:
        result += """

### Recommendation

These products belong to the same detected category.
Use the price and preference observations above as preliminary
comparison indicators.
"""

    result += """

*This prototype does not verify product quality, authenticity or performance.
OCR results may contain errors.*
"""

    return summary_a, summary_b, result


# =====================================
# USER INTERFACE
# =====================================

st.markdown("## 🌸 Product A")

col_a1, col_a2 = st.columns(2)

with col_a1:
    image_a = st.file_uploader(
        "Upload Product A photo",
        type=["jpg", "jpeg", "png"],
        key="image_a"
    )

    price_a = st.text_input(
        "Product A price (optional)",
        key="price_a"
    )

with col_a2:
    quantity_a = st.text_input(
        "Product A quantity / size (optional)",
        placeholder="e.g. 500 g, 128 GB"
    )

    if image_a:
        st.image(image_a, width=180)

st.markdown("---")
st.markdown("## 🩵 Product B")

col_b1, col_b2 = st.columns(2)

with col_b1:
    image_b = st.file_uploader(
        "Upload Product B photo",
        type=["jpg", "jpeg", "png"],
        key="image_b"
    )

    price_b = st.text_input(
        "Product B price (optional)",
        key="price_b"
    )

with col_b2:
    quantity_b = st.text_input(
        "Product B quantity / size (optional)",
        placeholder="e.g. 500 g, 128 GB"
    )

    if image_b:
        st.image(image_b, width=180)

st.markdown("---")

preferences = st.text_area(
    "What matters to you? (optional)",
    placeholder="e.g. Quality, value for money, durability..."
)

if st.button("✨ Compare Products", type="primary"):

    if image_a is None or image_b is None:
        st.error("Please upload photos for both products.")

    else:
        with st.spinner("Analysing products. Please wait..."):

            summary_a, summary_b, comparison = compare_products(
                {
                    "image": image_a,
                    "price": price_a,
                    "quantity": quantity_a
                },
                {
                    "image": image_b,
                    "price": price_b,
                    "quantity": quantity_b
                },
                preferences
            )

        st.markdown("## 📋 Product Summaries")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(summary_a)

        with col2:
            st.markdown(summary_b)

        st.markdown("---")
        st.markdown(comparison)
