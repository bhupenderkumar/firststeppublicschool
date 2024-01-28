from fpdf import FPDF
import datetime
import re
from utils import number_to_words
class PDF(FPDF):
    def header(self):
        self.image('school_logo.jpeg', 10, 8, 33)  # Adjust the numbers for position and size as needed
        self.set_xy(20, 10)  # Set position next to the logo
        self.set_font('Arial', '', 14)  # Reduce font size and remove bold
        self.cell(0, 8, 'FIRST STEP PUBLIC SCHOOL', 0, 1, 'C')
        self.cell(0, 10, '(Recognised)', 0, 1, 'C')  # Reduce font size and remove bold
        self.set_font('Arial', '', 10)  # Reduce font size
        self.cell(0, 8, 'H-164, Saurabh Vihar, Jaitpur, Delhi', 0, 1, 'C')
        self.cell(0, 8, 'Phone: 9667935518, 9717267473', 0, 1, 'C')  # Reduce font size
        website_text = 'Website: https://firststepschool.business.site/'
        self.cell(0, 8, website_text, 0, 1, 'C')  # Reduce font size
        x = (210 - self.get_string_width(website_text)) / 2  # 210 is the default A4 width in fpdf
        y = self.get_y() - 5  # Reduce the distance from the previous cell
        self.link(x, y, self.get_string_width(website_text), 8, 'https://firststepschool.business.site/')


    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'This is a computer-generated print', 0, 0, 'C')
        self.cell(0, 10, f'Page {str(self.page_no())}', 0, 0, 'C')

    def draw_dotted_line(self, length=190, spacing=1):
        current_y = self.get_y()
        for i in range(0, length, spacing * 1):
            self.line(10 + i, current_y, 10 + i + spacing, current_y)

    def create_receipt(self):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)

        # Dotted Line
        pdf.draw_dotted_line()
        pdf.ln(10)

        # Title
        pdf.cell(0, 10, 'Fee Receipt', 0, 1, 'C')
        pdf.ln(10)

        # Content
        pdf.set_font('Arial', '', 12)
        month = datetime.datetime.strptime(self["submit_date"], "%Y-%m-%d").strftime("%B")

        for key, value in self.items():
            if key == "_id" or key == "total_amount" or key == "collected_by" or key == "fee_type":  
                continue

            pdf.set_font('Arial', 'B', 12)  # Set font to bold for property names
            pdf.cell(50, 10, f"{re.sub(r'\\[\\d*\\]', '', key).replace('_', ' ').title()}: {key}", 0, 0, 'L')
            pdf.set_font('Arial', '', 12)  # Set font back to regular
            if "student_id" in key :
                pdf.cell(0, 10, f"{value[-4:]}", 0, 1, 'R')
            else:
                pdf.cell(0, 10, f"{value}", 0, 1, 'R')

        # Dotted Line
        pdf.draw_dotted_line()
        pdf.ln(10)

        # total_amount
        print(self)

        # Fee Type (if available)
        if 'collected_by' in self:
            pdf.cell(95, 10, "Collected By:", 0, 0, 'R')
            pdf.cell(0, 10, f" {self['collected_by']}", 0, 1, 'R')
            pdf.ln(5)

        # Total total_amount
        pdf.draw_dotted_line()
        pdf.cell(95, 10, "Total Amount:", 0, 0, 'R')
        pdf.cell(0, 10, f" {self['total_amount']}", 0, 1, 'R')
        pdf.cell(0, 10, f" {number_to_words(self['total_amount'])} Rupees only", 0, 1, 'R')

        # Dotted Line
        pdf.draw_dotted_line()
        pdf.ln(10)

        # Footer
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'Recognised by the Education Department', 0, 1, 'C')
        pdf.ln(5)

        # Output with dynamic filename
        filename = f"fee_receipt_{self['student_name']}_{self['fee_month']}.pdf"
        pdf.output(filename, 'F')
        return pdf

