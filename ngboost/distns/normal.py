from ngboost.distns import Distn
from ngboost.scores import LogScore, CRPScore
import scipy as sp
import numpy as np
from scipy.stats import norm as dist

class NormalLogScore(LogScore):
    def score(self, Y):
        return -self.dist.logpdf(Y)

    def d_score(self, Y):
        D = np.zeros((len(Y), 2))
        D[:, 0] = (self.loc - Y) / self.var
        D[:, 1] = 1 - ((self.loc - Y) ** 2) / self.var
        return D

    def metric(self):
        FI = np.zeros((self.var.shape[0], 2, 2))
        FI[:, 0, 0] = 1 / self.var + 1e-5
        FI[:, 1, 1] = 2
        return FI

class NormalCRPScore(CRPScore):
    def score(self, Y):
        Z = (Y - self.loc) / self.scale
        return (self.scale * (Z * (2 * sp.stats.norm.cdf(Z) - 1) + \
                2 * sp.stats.norm.pdf(Z) - 1 / np.sqrt(np.pi)))

    def d_score(self, Y):
        Z = (Y - self.loc) / self.scale
        D = np.zeros((len(Y), 2))
        D[:, 0] = -(2 * sp.stats.norm.cdf(Z) - 1)
        D[:, 1] = self.crps(Y) + (Y - self.loc) * D[:, 0]
        return D

    def metric(self):
        I = np.c_[2 * np.ones_like(self.var), np.zeros_like(self.var),
                  np.zeros_like(self.var), self.var]
        I = I.reshape((self.var.shape[0], 2, 2))
        I = 1 / (2 * np.sqrt(np.pi)) * I
        return I

class Normal(Distn):

    n_params = 2
    problem_type = "regression"
    scores = [NormalLogScore, NormalCRPScore]

    def __init__(self, params):
        super().__init__(params)
        self.loc = params[0]
        self.scale = np.exp(params[1])
        self.var = self.scale ** 2
        self.dist = dist(loc=self.loc, scale=self.scale)

    def __getattr__(self, name):
        if name in dir(self.dist):
            return getattr(self.dist, name)
        return None

    @property
    def params(self):
        return {'loc':self.loc, 'scale':self.scale}

    def fit(Y):
        m, s = sp.stats.norm.fit(Y)
        return np.array([m, np.log(s)])

    def sample(self, m):
        return np.array([self.rvs() for i in range(m)])

### Fixed Variance Normal ###
class NormalFixedVarLogScore(NormalLogScore):
    def d_score(self, Y):
        D = np.zeros((len(Y), 1))
        D[:, 0] = (self.loc - Y) / self.var
        return D

    def metric(self):
        FI = np.zeros((self.var.shape[0], 1, 1))
        FI[:, 0, 0] = 1 / self.var + 1e-5
        return FI

class NormalFixedVarCRPScore(NormalCRPScore):
    def d_score(self, Y):
        Z = (Y - self.loc) / self.scale
        D = np.zeros((len(Y), 1))
        D[:, 0] = -(2 * sp.stats.norm.cdf(Z) - 1)
        return D

    def metric(self): 
        I = np.c_[2 * np.ones_like(self.var)]
        I = I.reshape((self.var.shape[0], 1, 1))
        I = 1 / (2 * np.sqrt(np.pi)) * I
        return I

class NormalFixedVar(Normal):

    n_params = 1
    scores = [NormalFixedVarLogScore, NormalFixedVarCRPScore]

    def __init__(self, params):
        self.loc = params[0]
        self.var = np.ones_like(self.loc)
        self.scale = np.ones_like(self.loc)
        self.shape = self.loc.shape
        self.dist = dist(loc=self.loc, scale=self.scale)

    def fit(Y):
        m, s = sp.stats.norm.fit(Y)
        return m
