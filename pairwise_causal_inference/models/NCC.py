"""
Neural Causation Coefficient
Author : David Lopez-Paz
Ref :  Lopez-Paz, D. and Nishihara, R. and Chintala, S. and Schölkopf, B. and Bottou, L.,
    "Discovering Causal Signals in Images", CVPR 2017.
"""

from sklearn.preprocessing import scale
import numpy as np
import torch as th
from torch.autograd import Variable


class NCC_model(th.nn.Module):
    """ NCC models structure """

    def __init__(self, n_hiddens=20):
        """ Init the NCC structure with the number of hidden units

        :param n_hiddens: Number of hidden units
        :type n_hiddens: int
        """
        super(NCC_model, self).__init__()
        self.c1 = th.nn.Conv1d(2, n_hiddens, 1)
        self.c2 = th.nn.Conv1d(n_hiddens, n_hiddens, 1)
        self.batch_norm = th.nn.BatchNorm1d(n_hiddens, affine = False)
        self.l1 = th.nn.Linear(n_hiddens, n_hiddens)
        self.l2 = th.nn.Linear(n_hiddens, 1)

    def forward(self, x):
        """ Passing data through the network

        :param x: 2d tensor containing both (x,y) Variables
        :return: output of the net
        """
        act = th.nn.ReLU()
        out = act(self.c1(x))
        out = act(self.c2(out))
        out = act(self.l1(self.batch_norm(out)))
        return th.nn.Sigmoid(out)



class NCC(object):
    """Neural Causation Coefficient

    Infer causal relationships between pairs of variables
    Ref :  Lopez-Paz, D. and Nishihara, R. and Chintala, S. and Schölkopf, B. and Bottou, L.,
    "Discovering Causal Signals in Images", CVPR 2017.

    """
    def __init__(self):
        super(NCC, self).__init__()
        self.model = None

    def fit(self, x_tr, y_tr):
        """ Fit the NCC models

        :param x_tr: CEPC-format DataFrame containing pairs of variables
        :param y_tr: array containing targets
        """
        self.model = NCC_model()
        opt = th.optim.Adam(self.model.parameters())
        criterion = th.nn.BCELoss()
        if th.cuda.is_available():
            self.model = self.model.cuda()
        for idx, row in x_tr.iterrows():
            opt.zero_grad()
            a = row['A'].reshape((len(row['A']), 1))
            b = row['B'].reshape((len(row['B']), 1))
            m = np.hstack((a, b))
            m = scale(m)
            m = m.astype('float32')
            m = Variable(th.from_numpy(m))

            if th.cuda.is_available():
                m = m.cuda()

            out = self.model(m)
            loss = criterion(out, y_tr[idx])
            loss.backward()

            # NOTE : optim is called at each epoch ; might want to change
            opt.step()

    def predictor(self, a, b):
        """ Infer causal directions using the trained NCC models

        :param a: Variable 1
        :param b: Variable 2
        :return: probability (Value : 1 if a->b and -1 if b->a)
        :rtype: float
        """
        if not self.model():
            print('Model has to be trained before doing any predictions')
            raise ValueError

        m = np.hstack((a, b))
        m = scale(m)
        m = m.astype('float32')
        m = Variable(th.from_numpy(m))

        if th.cuda.is_available():
            m = m.cuda()

        return self.model(m)


