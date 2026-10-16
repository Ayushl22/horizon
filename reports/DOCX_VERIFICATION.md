# Word guide verification

The explanatory guide was authored only after UI implementation and verification were complete.

- Final file: Customer_Churn_Project_Explanation.docx.
- 26 rendered Letter-size pages, 23 chapters, a linked contents page and centred page numbers.
- Seven actual final-application screenshots embedded with descriptive alternate text. Source captures remain under ui_screenshots.
- Bold black headings and normal-weight body text, readable tables with repeating header rows and light borders.
- All actual metric tables derive from the preserved results.json. Small arithmetic examples are explicitly labelled as examples.
- The source discrepancy affecting seven charge-band records and uncertainty about their intended meaning are explained.
- Word was exported to an internal review PDF and all 26 pages rendered with Poppler and visually inspected individually. Blank-page, contents-number and inherited title-border defects were corrected.
- The standard render_docx.py helper was attempted but could not find bundled LibreOffice on Windows. An isolated invisible Word instance exported this artifact read-only instead, with no modification of other Word documents or the generated DOCX. The review PDF and page images are QA files under tmp/docx_review, not extra submission deliverables.
- Structural checks verify the DOCX package, 23 internal contents links/bookmarks, seven images, absence of the title border, 26 PDF pages, no blank pages, and the contents entry pointing to the actual final reference page.
- The pre-existing trained-model artifacts and ten-page PDF remain byte-for-byte unchanged.

The guide is a detailed learning and viva document, separate from the original ten-page PDF. Deployment and physical-device checks remain future instructions, not completed claims.
