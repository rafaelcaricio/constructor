import jsonschema
import os
import yaml


plan_schema="""

type: object
additionalProperties: true
properties:

  # resource definition
  resources:
    type: object
    properties:
      cpus:
        type: number
        minimum: 1
      memory:
        type: number
        minimum: 256

  # list of input definitions
  input:
    type: array
    items:
      type: object
      properties:
        type:
          type: string
          enum:
            - git
        source:
          type: string
          pattern: "^[a-z0-9@\\\\.:\\\\-/]+$"
        head:
          type: string
          pattern: "^[a-z0-9\\\\-/]+$"
        secret:
          type: string
          pattern: "^[a-z0-9-_/]+$"
        target:
          type: string
          pattern: "^[a-z0-9-_/]+$"
      required:
        - type
        - source
        - head
        - target

  # list of packages to install
  packages:
    type: array
    items:
      type: string
      pattern: "^[a-z0-9-\\\\.]+$"

  # list of work commands
  work:
    type: array
    items:
      type: object
      properties:
        cwd:
          type: string
          pattern: "^[a-z0-9-_/]+$"
        command:
          type: string
        environment:
          type: object
          additionalProperties:
            type: string
        root:
          type: bool
      required:
        - cwd
        - command

  # list of output definitions
  output:
    type: array
    items:
      type: object
      properties:
        type:
          type: string
          enum:
            - Docker
        source:
          type: string
          pattern: "^[a-z0-9-_/]+$"
        secret:
          type: string
          pattern: "^[a-z0-9-_/]+$"
        target:
          type: string
          pattern: "^[a-z0-9@\\\\.:\\\\-/]+$"
      required:
        - type
        - source
        - target

"""


def load_plan(stream):
    plan = yaml.load(stream)
    schema = yaml.load(plan_schema)
    jsonschema.validate(plan, schema)
    return plan


def discover_plan():
    # simple local file
    if os.path.isfile('/plan.yaml'):
        with open('/plan.yaml', 'r') as stream:
            return load_plan(stream)

    # Kubernetes metadata discovery: http://kubernetes.io/docs/user-guide/downward-api/
    # mount "downwardAPI" to "/kubernetes" with "annotations" from fieldPath "metadata.annotations"
    if os.path.isfile('/kubernetes/annotations'):
        with open('/kubernetes/annotations', 'r') as stream:
            # read key=value from /kubernetes/annotations
            # file looks like:
            #      key1="value1"
            #      key2=123
            #      key3="{\"foo\": \"bar\"}"
            # replace first = with : to make valid YAML out of it

            content = stream.read()
            content.replace('=', ': ', 1)
            annotations = yaml.load(content)

            # parse yaml from key "constructionPlan"
            return load_plan(annotations['constructionPlan'])

    raise Exception('could not discover any plans')