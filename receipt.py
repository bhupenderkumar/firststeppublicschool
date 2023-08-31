from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        self.image('school_logo.jpeg', 10, 8, 33)  # Adjust the numbers for position and size as needed
        self.set_xy(20, 10)  # Set position next to the logo
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'First Step Public School', 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'H-164, Saurabh Vihar, Jaitpur, Delhi', 0, 1, 'C')
        self.cell(0, 10, 'Phone: 9667935518', 0, 1, 'C')
        website_text = 'Website: https://firststepschool.business.site/'
        self.cell(0, 10, website_text, 0, 1, 'C')
        x = (210 - self.get_string_width(website_text)) / 2  # 210 is the default A4 width in fpdf
        y = self.get_y() - 10  # 10 is the height of the cell
        self.link(x, y, self.get_string_width(website_text), 10, 'https://firststepschool.business.site/')


    def footer(self):
        self.set_y(-30)  # Adjusting the y-position to make space for the new line
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'This is a computer-generated print', 0, 1, 'C')
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')


    def draw_dotted_line(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2)

    def create_receipt(data):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Fee Receipt', 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font('Arial', '', 12)
        month = datetime.datetime.strptime(data["submit_date"], "%Y-%m-%d").strftime("%B")
        for key, value in data.items():
            if key == "_id":  # Skip the _id field
                continue
            if key == "submit_date":  # Convert the date to month
                month = datetime.datetime.strptime(value, "%Y-%m-%d").strftime("%B")
                pdf.cell(0, 10, f"Month: {month}", 0, 1, 'L')
                continue
            pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {value}", 0, 1, 'L')

        # Dotted Line
        pdf.draw_dotted_line(10, 50, 200, 50)
        pdf.ln(5)
        pdf.cell(95, 10, "Amount:", 0, 0, 'R')
        pdf.cell(0, 10, f"Rupees {data['amount']}", 0, 1, 'R')
        pdf.draw_dotted_line(10, 60, 200, 60)
        pdf.ln(5)

        if data['fee__type']:
            pdf.cell(95, 10, "Fees Content:", 0, 0, 'R')
            pdf.cell(0, 10, f" {data['fee_type']}", 0, 1, 'R')
            pdf.ln(5)

        pdf.cell(95, 10, "Total Amount:", 0, 0, 'R')
        pdf.cell(0, 10, f"Rupees {data['amount']}", 0, 1, 'R')
        pdf.output('fee_receipt.pdf', 'F')
