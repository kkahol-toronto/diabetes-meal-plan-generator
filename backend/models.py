from pydantic import BaseModel
from typing import List, Optional

class ExtendedUserProfile(BaseModel):
    # Patient Demographics
    fullName: str
    dateOfBirth: str
    age: int
    sex: str
    ethnicity: List[str]

    # Medical History
    medicalHistory: List[str]

    # Current Medications
    currentMedications: List[str]

    # Most Recent Lab Values
    a1c: Optional[float] = None
    fastingGlucose: Optional[float] = None
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    triglycerides: Optional[float] = None
    totalCholesterol: Optional[float] = None
    egfr: Optional[float] = None
    creatinine: Optional[float] = None
    potassium: Optional[float] = None
    uacr: Optional[float] = None
    altAst: Optional[float] = None
    vitaminD: Optional[float] = None
    b12: Optional[float] = None

    # Vital Signs
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    bloodPressureSys: Optional[int] = None
    bloodPressureDia: Optional[int] = None
    heartRate: Optional[int] = None

    # Dietary Information
    typeOfDiet: str
    dietaryFeatures: List[str]
    dietaryAllergies: str
    strongDislikes: str

    # Physical Activity Profile
    workActivity: str
    exerciseFrequency: str
    exerciseTypes: List[str]
    mobilityIssues: bool

    # Lifestyle & Preferences
    mealPrepCapability: str
    appliances: List[str]
    eatingSchedule: str
    eatingScheduleOther: str

    # Goals & Readiness to Change
    primaryGoals: List[str]
    readinessToChange: str

    # Meal Plan Targeting
    weightLossDesired: bool
    suggestedCalorieTarget: Optional[int] = None
    suggestedCalorieOther: Optional[int] = None 