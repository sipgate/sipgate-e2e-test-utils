from prometheus_client.parser import text_string_to_metric_families


def count_metric(metrics: str, metric_name: str, labels: dict[str, str] | None = None) -> float:
    """
    When supplied with an arbitrary number of metrics in prometheus format,
    this method calculates the sum of the given counter or gauge, filtering by the given labels.
    """

    family = next((f for f in text_string_to_metric_families(metrics) if metric_name == f.name or (f.type == 'counter' and metric_name == f'{f.name}_total')), None)

    if family is None:
        return 0

    if family.type not in ['gauge', 'counter']:
        raise ValueError(f'unsupported metric type "{family.type}"')

    return sum((float(s.value) for s in family.samples if labels is None or labels.items() <= s.labels.items()))
