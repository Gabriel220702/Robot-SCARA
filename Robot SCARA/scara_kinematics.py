import numpy as np
from math import radians, degrees, cos, sin, sqrt, acos, atan2

# --- CONSTANTES CINEMÁTICAS ---
L1 = 28.9818176
L2 = 12.4700356
D1_OFFSET = 13.6
Z_TRAVEL = 5.5
EPSILON = 0.1

class ScaraRobot:
    def __init__(self):
        self.L1 = L1
        self.L2 = L2
        self.D1_OFFSET = D1_OFFSET
        self.Z_TRAVEL = Z_TRAVEL
        self.q1 = 0.0
        self.q2 = 0.0
        self.z = 0.0

    def forward_kinematics(self, q1_deg, q2_deg, q3_val):
        self.q1 = q1_deg
        self.q2 = q2_deg
        self.z = q3_val
        q1 = radians(q1_deg)
        q2 = radians(q2_deg)
        q12 = q1 + q2
        c1 = cos(q1); s1 = sin(q1)
        c12 = cos(q12); s12 = sin(q12)
        x_codo = self.L1 * c1
        y_codo = self.L1 * s1
        x_final = x_codo + self.L2 * c12
        y_final = y_codo + self.L2 * s12
        z_final = self.D1_OFFSET - q3_val

        matrix_T = [
            c12, -s12, 0, x_final,
            s12,  c12, 0, y_final,
            0,    0,   1, z_final,
            0,    0,   0, 1
        ]
        return { "codo": {"x": x_codo, "y": y_codo}, "final": {"x": x_final, "y": y_final, "z": z_final}, "matrix": matrix_T }

    def inverse_kinematics(self, x, y, z_target):
        d3_cm = self.D1_OFFSET - z_target 
        if not (-EPSILON <= d3_cm <= self.Z_TRAVEL + EPSILON): return None 
        R_sq = x**2 + y**2
        R = sqrt(R_sq)
        max_reach = self.L1 + self.L2
        min_reach = abs(self.L1 - self.L2)
        if R > max_reach + EPSILON or R < min_reach - EPSILON: return None 
        cos_q2 = (R_sq - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        cos_q2 = max(min(cos_q2, 1.0 - EPSILON), -1.0 + EPSILON)
        q2_rad = acos(cos_q2)
        alfa = atan2(y, x)
        beta = atan2(self.L2 * sin(q2_rad), self.L1 + self.L2 * cos(q2_rad))
        q1_rad = alfa - beta
        return degrees(q1_rad), degrees(q2_rad), d3_cm
