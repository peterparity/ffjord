import torch
import torch.nn as nn

from integrate import odeint_adjoint as odeint

__all__ = ["CNF"]


class CNF(nn.Module):
    def __init__(self, odefunc):
        super(CNF, self).__init__()
        self.odefunc = odefunc
        self.register_parameter("end_time", nn.Parameter(torch.tensor([0.3])))
        self.odefunc._num_evals = 0

    def forward(self, z, logpz=None, integration_times=None, reverse=False, atol=1e-6, rtol=1e-5):
        if logpz is None:
            _logpz = torch.zeros(z.shape[0], 1).to(z)
        else:
            _logpz = logpz

        if integration_times is None:
            integration_times = torch.cat([torch.tensor([0.]).to(self.end_time), self.end_time])
        if reverse:
            integration_times = _flip(integration_times, 0)

        # Fix noise throughout integration.
        self.odefunc.before_odeint(e=torch.randn(z.shape).to(z.device))
        z_t, logpz_t = odeint(self.odefunc, (z, _logpz), integration_times.to(z), atol=atol, rtol=rtol)

        if len(integration_times) == 2:
            z_t, logpz_t = z_t[1], logpz_t[1]

        if logpz is not None:
            return z_t, logpz_t
        else:
            return z_t

    def num_evals(self):
        return self.odefunc._num_evals


def _flip(x, dim):
    indices = [slice(None)] * x.dim()
    indices[dim] = torch.arange(x.size(dim) - 1, -1, -1, dtype=torch.long, device=x.device)
    return x[tuple(indices)]
