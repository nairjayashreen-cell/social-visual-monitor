@app.get("/scan")
def scan():

    try:

        url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_TOKEN}"

        response = requests.get(url)

        print("APIFY STATUS:", response.status_code)

        data = response.json()

        print("TOTAL ITEMS:", len(data))

        results = []

        reference_image = f"{UPLOAD_DIR}/reference_logo.png"

        if not os.path.exists(reference_image):

            return {
                "error": "Reference image not found"
            }

        for item in data:

            try:

                image_url = item.get("displayUrl", "")

                print("IMAGE URL:", image_url)

                if not image_url:
                    continue

                temp_image_path = f"{UPLOAD_DIR}/temp.jpg"

                img_data = requests.get(image_url).content

                with open(temp_image_path, "wb") as handler:
                    handler.write(img_data)

                similarity = compare_images(
                    reference_image,
                    temp_image_path
                )

                print("SIMILARITY:", similarity)

                if similarity > 0.25:

                    results.append({

                        "platform": "Instagram",

                        "username": item.get(
                            "ownerUsername",
                            "unknown"
                        ),

                        "url": item.get(
                            "url",
                            ""
                        ),

                        "brand": "Creative Match Found",

                        "score": f"{round(similarity * 100)}%",

                        "risk": "Critical",

                        "ocr": item.get(
                            "caption",
                            ""
                        )[:200],

                        "time": item.get(
                            "timestamp",
                            "recent"
                        ),

                        "image": image_url

                    })

            except Exception as item_error:

                print("ITEM ERROR:", item_error)

                continue

        return results

    except Exception as e:

        print("SCAN ERROR:", e)

        return {
            "error": str(e)
        }
