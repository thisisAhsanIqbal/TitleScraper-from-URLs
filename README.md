# Async URL Title Scraper

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blueviolet)

An efficient asynchronous Python tool to fetch the **H1 heading** or **page title** from a list of URLs and save the results to an Excel file.

Built with `aiohttp`, `asyncio`, `BeautifulSoup`, and `pandas`, this scraper can handle **large batches of URLs** with controlled concurrency and timeout settings.

---

## 🚀 Features
- Fetches either `<h1>` tag text or `<title>` tag if `<h1>` not available
- Handles HTTP errors and unexpected exceptions gracefully
- Asynchronous requests using `aiohttp` and `asyncio`
- Saves output in a timestamped Excel file
- Progress tracking with `tqdm`
- Supports large input files by chunking
- Automatic fallback to CSV if Excel writing fails

---

## 📂 Input Requirements
1. A text file named like:

urls.txt

---

## ✍️ Script Compiled by Muhammad Ahsan Iqbal

- **LinkedIn:** [https://www.linkedin.com/in/ahsan-iqbal-digitalmarketingexpert/](https://www.linkedin.com/in/ahsan-iqbal-digitalmarketingexpert/)
- **GitHub:** [https://github.com/thisisAhsanIqbal](https://github.com/thisisAhsanIqbal)

---
