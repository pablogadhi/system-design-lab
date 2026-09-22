[38;2;0;136;0;03m# pipelines/ — stream processing jobs[39;00m

[38;2;170;34;255;01mOne[39;00m[38;2;187;187;187m [39mfolder[38;2;187;187;187m [39mper[38;2;187;187;187m [39mjob,[38;2;187;187;187m [39mlisted[38;2;187;187;187m [39munder[38;2;187;187;187m [39m`pipelines:`[38;2;187;187;187m [39m[38;2;170;34;255;01min[39;00m[38;2;187;187;187m [39m`stack.yaml`.[38;2;187;187;187m [39m[38;2;170;34;255;01mEach[39;00m[38;2;187;187;187m [39mhas[38;2;187;187;187m [39mits[38;2;187;187;187m [39mown[38;2;187;187;187m [39m`Tiltfile`[38;2;187;187;187m [39m(included[38;2;187;187;187m [39m[38;2;170;34;255;01mby[39;00m
the[38;2;187;187;187m [39mroot[38;2;187;187;187m [39mTiltfile)[38;2;187;187;187m [39mthat[38;2;187;187;187m [39mbuilds[38;2;187;187;187m [39mthe[38;2;187;187;187m [39mjob[38;2;187;187;187m [39mimage[38;2;187;187;187m [39m[38;2;170;34;255;01mand[39;00m[38;2;187;187;187m [39mdeploys[38;2;187;187;187m [39mit[38;2;187;187;187m [39m—[38;2;187;187;187m [39m[38;2;170;34;255;01mfor[39;00m[38;2;187;187;187m [39mFlink,[38;2;187;187;187m [39ma[38;2;187;187;187m [39m`FlinkDeployment`[38;2;187;187;187m [39m[38;2;170;34;255;01min[39;00m[38;2;187;187;187m [39mnamespace
`apps`[38;2;187;187;187m [39m(see[38;2;187;187;187m [39mthe[38;2;187;187;187m [39mflink[38;2;187;187;187m [39m[38;2;170;34;255;01mrow[39;00m[38;2;187;187;187m [39m[38;2;170;34;255;01min[39;00m[38;2;187;187;187m [39m`infra/components/PLAYBOOK.md`).[38;2;187;187;187m [39mOwned[38;2;187;187;187m [39m[38;2;170;34;255;01mby[39;00m[38;2;187;187;187m [39mthe[38;2;187;187;187m [39mservices[38;2;102;102;102m-[39mbuilder[38;2;187;187;187m [39magent.

```
pipelines/<name>/
├── Tiltfile          # docker_build(...) + k8s_yaml('deploy/flinkdeployment.yaml')
├── Dockerfile        # FROM flink:<pinned> + job (PyFlink or SQL runner)
├── job/              # the job code (Flink SQL / PyFlink)
├── deploy/           # FlinkDeployment (parallelism, checkpointing, env from <component>-conn secrets)
└── README.md         # what it computes, delivery guarantees, how to observe it
```
[38;2;170;34;255;01mEmpty[39;00m[38;2;187;187;187m [39m[38;2;170;34;255;01min[39;00m[38;2;187;187;187m [39mthe[38;2;187;187;187m [39mtemplate.
