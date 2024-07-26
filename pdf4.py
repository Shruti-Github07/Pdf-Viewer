
import uuid

def save_signature(self):
    if not self.signature_label:
        return

    # Get the position of the signature image relative to the pdfDisplay
    sig_pos = self.signature_label.pos() - self.pdfDisplay.pos()
    sig_rect = QRect(sig_pos, self.signature_label.size())

    # Get the current page
    page = self.doc.load_page(self.current_page)

    # Convert the QRect to a position in the PDF
    pdf_x0 = sig_rect.left() * page.rect.width / self.pdfDisplay.width()
    pdf_y0 = sig_rect.top() * page.rect.height / self.pdfDisplay.height()
    pdf_x1 = sig_rect.right() * page.rect.width / self.pdfDisplay.width()
    pdf_y1 = sig_rect.bottom() * page.rect.height / self.pdfDisplay.height()

    # Save the signature image to a unique temporary file
    temp_image_path = f"temp_signature_{uuid.uuid4().hex}.png"
    self.signature_image.save(temp_image_path)

    # Create a PDF image
    img_rect = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)
    page.insert_image(img_rect, filename=temp_image_path)

    # Clean up the temporary file
    os.remove(temp_image_path)

# Update the import statements at the top of the file
import sys
import os
import uuid
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from main_window import Ui_MainWindow
import fitz

class PDFReader(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.open_pdf)
        self.actionDark_Mode.triggered.connect(self.setDarkMode)
        self.actionLight_Mode.triggered.connect(self.setLightMode)
        self.actionwrite.triggered.connect(self.toggle_writing_mode)
        self.actionSave.triggered.connect(self.save_drawing)
        self.actionSave_As.triggered.connect(self.save_as_drawing)
        self.actionUndo.triggered.connect(self.undo)
        self.actionRedo.triggered.connect(self.redo)
        self.actionExit.triggered.connect(self.exit_app)
        self.nextButton.clicked.connect(self.next_page)
        self.prevButton.clicked.connect(self.prev_page)
        self.actionAdd_signature.triggered.connect(self.toggle_signature_mode)
        self.doc = None
        self.current_page = 0
        self.drawing = False
        self.last_point = QPoint()
        self.writing_mode = False
        self.signature_mode = False
        self.signature_image = None
        self.signature_label = None

        self.page_drawings = {}
        self.undo_stack = []
        self.redo_stack = []
 
        # Adjust window size to fit within screen dimensions
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.setGeometry(0, 0, int(screen_geometry.width() * 0.8), int(screen_geometry.height() * 0.8))
        self.setMinimumSize(int(screen_geometry.width() * 0.5), int(screen_geometry.height() * 0.5))

        # Adjust pdfDisplay size dynamically
        self.pdfDisplay.setGeometry(QRect(10, 10, self.width() - 20, self.height() - 100))

    def resizeEvent(self, event):
        # Resize pdfDisplay dynamically when the main window is resized
        self.pdfDisplay.setGeometry(QRect(10, 10, self.width() - 20, self.height() - 100))
        if self.doc:
            self.show_page()
        super().resizeEvent(event)

    def open_pdf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.doc = fitz.open(fileName)
            self.current_page = 0
            self.show_page()

    def show_page(self):
        if self.doc:
            page = self.doc.load_page(self.current_page)
            pix = page.get_pixmap()
            qt_img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)

            if self.current_page in self.page_drawings:
                painter = QPainter(pixmap)
                painter.drawPixmap(0, 0, self.page_drawings[self.current_page])
                painter.end()

            self.pdfDisplay.setPixmap(pixmap)

    def next_page(self):
        if self.doc and self.current_page < len(self.doc) - 1:
            self.save_current_drawing()
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.save_current_drawing()
            self.current_page -= 1
            self.show_page()

    def save_current_drawing(self):
        current_pixmap = self.pdfDisplay.pixmap()
        if current_pixmap:
            self.page_drawings[self.current_page] = current_pixmap.copy()

    def setDarkMode(self):
        self.setStyleSheet('''QWidget{
            background-color: rgb(33,33,33);
            color: #FFFFFF;
            }
            QPushButton{
                background-color: #FFFFFF;
                color: #000000;           
            }
            QMenuBar::item:selected{
            color: #000000
            } ''')

    def setLightMode(self):
        self.setStyleSheet("")

    def toggle_writing_mode(self):
        self.writing_mode = not self.writing_mode
        if self.writing_mode:
            self.actionwrite.setText("Exit Writing Mode")
        else:
            self.actionwrite.setText("Write")

    def mousePressEvent(self, event):
        if self.writing_mode and event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.undo_stack.append(self.pdfDisplay.pixmap().copy())
            self.redo_stack.clear()
        elif self.signature_mode and event.button() == Qt.LeftButton and self.signature_label:
            self.offset = event.pos() - self.signature_label.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and self.writing_mode and event.buttons() & Qt.LeftButton:
            painter = QPainter(self.pdfDisplay.pixmap())
            pen = QPen(Qt.blue, 2.3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()
        elif self.signature_mode and self.signature_label and event.buttons() & Qt.LeftButton:
            self.signature_label.move(event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False

    def toggle_signature_mode(self):
        self.signature_mode = not self.signature_mode
        if self.signature_mode:
            self.load_signature_image()
        else:
            if self.signature_label:
                self.save_signature()
                self.signature_label.setParent(None)
                self.signature_label = None
                self.show_page()  # Refresh the page to show the saved signature

    def load_signature_image(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Signature Image", "", "Image Files (*.png *.jpg *.bmp);;All Files (*)", options=options)
        if fileName:
            self.signature_image = QPixmap(fileName)
            self.signature_label = QLabel(self)
            self.signature_label.setPixmap(self.signature_image)
            # self.signature_label.setGeometry(100, 100, 200, 125)
            self.signature_label.setGeometry(100, 100, self.signature_image.width(), self.signature_image.height())
            self.signature_label.setScaledContents(True)
            self.signature_label.setStyleSheet("background: transparent;")
            self.signature_label.show()

    def save_signature(self):
        if not self.signature_label:
            return

        # Get the position of the signature image relative to the pdfDisplay
        sig_pos = self.signature_label.pos() - self.pdfDisplay.pos()
        sig_rect = QRect(sig_pos, self.signature_label.size())

        # Get the current page
        page = self.doc.load_page(self.current_page)

        # Convert the QRect to a position in the PDF
        pdf_x0 = sig_rect.left() * page.rect.width / self.pdfDisplay.width()+250
        pdf_y0 = sig_rect.top() * page.rect.height / self.pdfDisplay.height()
        pdf_x1 = sig_rect.right() * page.rect.width / self.pdfDisplay.width() +250
        pdf_y1 = sig_rect.bottom() * page.rect.height / self.pdfDisplay.height() 

        # Save the signature image to a unique temporary file
        temp_image_path = f"temp_signature_{uuid.uuid4().hex}.png"
        self.signature_image.save(temp_image_path)

        # Create a PDF image
        img_rect = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)
        page.insert_image(img_rect, filename=temp_image_path)

        # Clean up the temporary file
        os.remove(temp_image_path)

    def save_drawing(self):
        pass

    def save_as_drawing(self):
        if not self.doc:
            return

        options = QFileDialog.Options()
        save_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if save_path:
            for page_number in range(len(self.doc)):
                page = self.doc.load_page(page_number)
                pix = page.get_pixmap()
                qt_img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                combined_pixmap = QPixmap.fromImage(qt_img)
                
                painter = QPainter(combined_pixmap)
                if page_number in self.page_drawings:
                    painter.drawPixmap(0, 0, self.page_drawings[page_number])
                painter.end()

                combined_image_path = "combined_temp_image.png"
                combined_pixmap.save(combined_image_path)

                rect = page.rect
                page.clean_contents()
                page.insert_image(rect, filename=combined_image_path)

            self.doc.save(save_path)
            print(f"Changes saved to the new file: {save_path}")

            os.remove(combined_image_path)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.pdfDisplay.pixmap().copy())
            last_pixmap = self.undo_stack.pop()
            self.pdfDisplay.setPixmap(last_pixmap)
            self.update()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.pdfDisplay.pixmap().copy())
            next_pixmap = self.redo_stack.pop()
            self.pdfDisplay.setPixmap(next_pixmap)
            self.update()

    def exit_app(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = PDFReader()
    reader.show()
    sys.exit(app.exec_())
