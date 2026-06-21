from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

class OCREngine:
    def __init__(self):
        print("🚀 Đang khởi tạo mô hình OCR...")
        # 1. Khởi tạo PaddleOCR (Chỉ dùng để detect khung chữ)
        self.paddle = PaddleOCR(use_angle_cls=True, lang="vi", det_db_box_thresh=0.6, drop_score=0.5)

        # 2. Khởi tạo VietOCR (Dùng để nhận diện chữ trong khung)
        config = Cfg.load_config_from_name('vgg_transformer')
        config['cnn']['pretrained'] = False
        config['device'] = 'cpu' # Hoặc 'cuda:0' nếu có GPU
        self.vietocr = Predictor(config)

ocr_engine = OCREngine()