from dataclasses import dataclass
import numpy as np

from .contracts import LearningRow, Probe


@dataclass(frozen=True)
class HaulQuantile:
    parameters: np.ndarray
    output_scale: float
    reference: float
    loss: float
    accepted_count: int
    percentile: float = .78

    def predict(self, probe: Probe) -> float:
        regressors = carrier_terms(probe.standard)
        return max(0, (regressors @ self.parameters) * self.output_scale)

    def describe(self) -> dict:
        return {'quantile': self.percentile, 'pinball_loss_kg': self.loss, 'learned_weights': self.parameters.tolist(),
                'scale_kg': self.output_scale, 'uniform_quantile_kg': self.reference, 'weighings': self.accepted_count}


def carrier_terms(signal: tuple[float, ...]) -> np.ndarray:
    portion, occupancy, meals, since_last, detour = signal
    interaction = max(0, occupancy) * max(0, since_last)
    return np.array([1, portion, occupancy, meals, since_last, detour, interaction])


def fit_estimator(rows: tuple[LearningRow, ...]) -> HaulQuantile:
    features = np.stack([carrier_terms(record.probe.standard) for record in rows])
    weights = np.array([1/(1 + record.probe.raw[-1]/160) for record in rows])
    targets = np.array([record.outcome for record in rows])
    output_scale = max(1.0, float(np.median(targets)))
    normalized = targets / output_scale
    percentile = .78
    reference = float(np.quantile(targets, percentile))
    coefficients = np.zeros(features.shape[1])
    coefficients[0] = reference / output_scale
    regularization = np.full_like(coefficients, .016)
    regularization[0] = 0
    for iteration in range(740):
        difference = normalized - features @ coefficients
        derivative = np.where(difference >= 0, -percentile, 1-percentile) * weights
        gradient = features.T @ derivative / weights.sum() + regularization * coefficients
        step = .104 / (1 + iteration / 72) ** .83
        coefficients -= step * gradient
    errors = targets - (features @ coefficients) * output_scale
    loss = np.mean(np.maximum(percentile * errors, (percentile - 1)*errors))
    return HaulQuantile(coefficients, output_scale, reference, float(loss), len(rows), percentile)
