from crewai import LLM
import inspect

print("LLM methods:")
for name, method in inspect.getmembers(LLM, predicate=inspect.isfunction):
    print(name)
