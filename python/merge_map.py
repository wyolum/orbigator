from pypdf import PdfWriter

writer = PdfWriter()
pdfs = [
    'vector_map_bowl_sheet_1.pdf',
    'vector_map_bowl_sheet_2.pdf',
    'vector_map_bowl_sheet_3.pdf',
    'vector_map_bowl_sheet_4.pdf',
]

for pdf in pdfs:
    writer.append(pdf)

out = "vector_map_bowl.pdf"
with open(out, "wb") as f:
    writer.write(f)

print("wrote", out)
