from torch.utils.data import Dataset
import os
import cfg
import PIL.Image as Image
from torchvision import transforms
import numpy as np
import math
from utils import one_hot, stack_cls


class Dataset(Dataset):
    def __init__(self):
        super().__init__()
        self.trans = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
        ])
        self.IMAGE_PATH = cfg.IMAGE_PATH
        with open(cfg.TEXT_PATH) as text:
            self.dataset = text.readlines()

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        labels = {}
        str = self.dataset[index]
        strs = str.strip().split()
        image_data = self.trans(Image.open(os.path.join(self.IMAGE_PATH, strs[0])))
        boxes = np.array([float(x) for x in strs[1:]])
        boxes = np.split(boxes, len(boxes) // 5)
        boxes = stack_cls(np.stack(boxes))

        for feature_size, anchors in cfg.ANCHORS_GROUP.items():
            labels[feature_size] = np.zeros([feature_size, feature_size, 3, 5 + cfg.CLASS_NUM], dtype=np.float32)
            for box in boxes:
                center_x, center_y, w, h, cls = box
                # 获得中心的的偏移量以及索引值
                offset_x, x_index = math.modf(center_x * feature_size / cfg.IMAGE_SIZE)
                offset_y, y_index = math.modf(center_y * feature_size / cfg.IMAGE_SIZE)
                for i, anchor in enumerate(anchors):
                    anchor_area = cfg.ANCHORS_GROUP_AREA[feature_size][i]  # 建议框面积
                    p_w, p_h = np.log(w / anchor[0]), np.log(h / anchor[1])  # 宽和高的偏移量
                    real_area = w * h  # 真实框的面积
                    conf = np.minimum(anchor_area, real_area) / np.maximum(anchor_area, real_area)
                    labels[feature_size][int(x_index), int(y_index), i] = np.array([offset_x, offset_y, p_w, p_h, conf,
                                                                                    *one_hot(cfg.CLASS_NUM, cls)])
        return labels[13], labels[26], labels[52], image_data


if __name__ == '__main__':
    data = Dataset()

    for i in range(5):
        a, b, c, d = data[i]
        mask_a = np.where(a[..., 4] > 0)
        # mask_b = np.where(b[..., 4] > 0)
        # mask_c = np.where(c[..., 4] > 0)
        print(a[mask_a])
        print()
    # print(b[mask_b])
    # print(c[mask_c])
    # print(a[10][7][2])
    # print(a[7][10][2])
