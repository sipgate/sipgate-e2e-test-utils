# sipgate Python E2E-Test Utils

This is a Python library for common utils used in sipgate-specific E2E testing (XML-, JSON-RPC, awaiting assertions, JobD helpers).

## Usage
In order to include this module in your project, add e.g.

```requirements
sipgate_e2e_test_utils @ git+https://github.com/sipgates/sipgate-e2e-test-utils.git@main
```

to your `requirements.txt`.
This will only allow you to use certain features like waiting utilities and RPC request/response parsing/serialization. 

Other features, which require additional dependencies to be installed, can be enabled by using "extras".
For example, to activate the `jobd` and `metrics` features, add:

```requirements
sipgate_e2e_test_utils[jobd,metrics] @ git+https://github.com/sipgates/sipgate-e2e-test-utils.git@main
```

### Available extras

#### jobd

Trigger JobD jobs and record their answer.

```python
from sipgate_e2e_test_utils.jobd import JobD

async def test_something():
    async with JobD(system_hostname='localhost', system_port=8080) as jobd:
        job_result = await jobd.trigger_job_and_record_answer('any_job')

        assert 'success' in job_result
```

#### rpc_matchers

Use in conjunction with [HttpRequestRecorder](https://github.com/sipgate/http-request-recorder.git) to expect XML- and JSON-RPC requests.

```python
from http_request_recorder import HttpRequestRecorder
from sipgate_e2e_test_utils.rpc_matchers import json_rpc
from sipgate_e2e_test_utils.json_rpc import JsonRpcResponse, JsonRpcRequest


async def test_something():
    async with HttpRequestRecorder(name='a-service', port=3000) as system:
        exp = system.expect(json_rpc('jsonrpc.method-name'), JsonRpcResponse.result(200, 'ok'))

        # trigger some code calling 'jsonrpc.method-name'

        request = JsonRpcRequest.parse(await exp.wait())
```

#### db

Add helpers to clear databases using SQLAlchemy, for example in preparation of test runs.
A `Base = declarative_base()` is required to find the tables to be cleared.

```python
from sqlalchemy import create_engine
from sipgate_e2e_test_utils.db import clear_all_tables

db_engine = create_engine('mysql+pymysql://user:password@db.host/db-name')
clear_all_tables(db_engine, Base)
```

#### metrics

Allows to count a metric with optional labels from a prometheus-style metrics response.

```python
from sipgate_e2e_test_utils.metrics import count_metric

metrics = "..."  # fetch for example with HTTP

count = count_metric(metrics, 'the_metric_name', { 'a_label': 'a_value' })
```
