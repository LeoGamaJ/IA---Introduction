# Gemini API Scripts

This repository contains three Python scripts that demonstrate how to interact with the Gemini API, a powerful language model developed by Google. Each script showcases a different level of complexity in the API usage, allowing you to learn and progress your understanding gradually.

## Scripts

1. **main.py**
   - This script provides a simple example of how to make a basic call to the Gemini API to generate text based on a user prompt.
   - It loads the necessary API key from an `.env` file and includes a basic error handling mechanism.

2. **main2.py**
   - This script introduces a more advanced approach to interacting with the Gemini API.
   - It includes a `GeminiAPI` class that encapsulates the API configuration and provides methods for generating content with various customization options, such as temperature, top-k, top-p, and stop sequences.
   - The script also includes a menu-driven interface that allows the user to easily adjust the configuration settings.

3. **main3.py**
   - This script demonstrates the most comprehensive usage of the Gemini API, covering a wide range of content types, including text, images, PDFs, Markdown, HTML, and code.
   - It includes a `MediaHandler` class that processes different types of content for submission to the API.
   - The script also provides an advanced command-line interface with additional features, such as the ability to send files and dynamically adjust the Gemini model.

## Prerequisites

To use these scripts, you'll need the following:

1. A Google Cloud account with the Gemini API enabled.
2. An API key for the Gemini API, which you can obtain from the Google Cloud Console.
3. The following Python packages installed:
   - `requests`
   - `python-dotenv`
   - `enum34` (for Python versions before 3.4)
   - `markdown` (for the `main3.py` script)
   - `pygments` (for the `main3.py` script)
   - `beautifulsoup4` (for the `main3.py` script)
   - `pillow` (for the `main3.py` script)
   - `PyMuPDF` (optional, for PDF support in the `main3.py` script)

You can install the required packages using pip:

```
pip install -r requirements.txt
```

## Usage

1. Clone the repository to your local machine.
2. Create a `.env` file in the same directory as the scripts and add your Gemini API key:

   ```
   GEMINI_API_KEY=your_api_key_here
   ```

3. Run the scripts:
   - `python main.py`: Runs the basic Gemini API script.
   - `python main2.py`: Runs the advanced Gemini API script with configuration options.
   - `python main3.py`: Runs the comprehensive Gemini API script with support for various content types.

Enjoy exploring the capabilities of the Gemini API through these sample scripts!

## Contributing

Contributions are welcome! If you have suggestions, improvements or fixes, feel free to open a pull request or report an issue.

## License

This project is under MIT license. See the [LICENSE](LICENSE) file for details.

---

If you have any questions or problems, please get in touch via [leo@leogama.cloud](mailto:leo@leogama.cloud)

