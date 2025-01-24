import numpy as np

class Muscle:
    def __init__(self):
        '''
        설멍:
        muscle의 passive component를 적용하기 위해서 
        '''
        self.angle = 0
        self.velocity = 0
        self.neutral_torque = 0
        pass

    def M_stiffness(self):
        '''
        angle : Unit[deg]
        '''
        if self.angle >= -5 and self.angle  <= 55:
            torque = 22.5*np.exp(-0.0367*self.angle)
        elif self.angle >= 55 and self.angle <= 95:
            torque = -0.149*self.angle + 11.17
        elif self.angle >= 95 and self.angle <= 155:
            torque = -0.002*np.exp(0.0768*self.angle)
        else:
            torque = 0
        return torque

    def M_damping(self):
        
        def damping_coef(angle):
            coef = 0.000213 * angle ^ 2 - 0.0266* angle + 1.583
            return coef
        
        torque = damping_coef(self.angle) * self.velocity

        return torque
    
    def M_passive(self):

        total_torque = self.M_damping() + self.M_stiffness()
        return total_torque
    
    def M_active(self):
        torque = 0
        return torque
