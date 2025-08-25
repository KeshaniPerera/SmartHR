from rest_framework import serializers
from .constants import PREHIRE_FEATURES

class PrehireInputSerializer(serializers.Serializer):
    # NEW meta fields (not used by the model)
    CandidateID = serializers.CharField(max_length=64)
    CandidateName = serializers.CharField(max_length=120)

    # existing feature fields
    Age = serializers.IntegerField(min_value=16, max_value=80)
    Gender = serializers.ChoiceField(choices=["Male", "Female"])
    BusinessTravel = serializers.ChoiceField(choices=["Travel_Rarely","Travel_Frequently","Non-Travel"])
    Department = serializers.ChoiceField(choices=["Sales","Research & Development","Human Resources"])
    Education = serializers.IntegerField(min_value=1, max_value=5)
    EducationField = serializers.ChoiceField(choices=["Life Sciences","Medical","Marketing","Technical Degree","Human Resources","Other"])
    JobRole = serializers.ChoiceField(choices=[
        "Sales Executive","Research Scientist","Laboratory Technician","Manufacturing Director",
        "Healthcare Representative","Manager","Sales Representative","Research Director","Human Resources"
    ])
    MaritalStatus = serializers.ChoiceField(choices=["Single","Married","Divorced"])
    DistanceFromHome = serializers.IntegerField(min_value=0, max_value=100)
    TotalWorkingYears = serializers.IntegerField(min_value=0, max_value=60)
    NumCompaniesWorked = serializers.IntegerField(min_value=0, max_value=20)
    StockOptionLevel = serializers.IntegerField(min_value=0, max_value=3)
    TrainingTimesLastYear = serializers.IntegerField(min_value=0, max_value=20)

    def to_feature_dict(self):
        d = self.validated_data
        # only model features (excludes CandidateID/Name)
        return {k: d.get(k) for k in PREHIRE_FEATURES}

    def meta(self):
        d = self.validated_data
        return {
            "candidate_id": d.get("CandidateID"),
            "candidate_name": d.get("CandidateName"),
        }
