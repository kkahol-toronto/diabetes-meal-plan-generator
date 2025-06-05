const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());            // allow React dev server on localhost:3000
app.use(express.json());

let savedProfile = null;

app.get('/api/profile/get', (req, res) => {
  if (!savedProfile) {
    return res.sendStatus(404);
  }
  res.json(savedProfile);
});

app.post('/api/profile/save', (req, res) => {
  const data = req.body;

  // Define required fields
  const requiredFields = [
    'fullName','dateOfBirth','age','sex','ethnicity','medicalHistory',
    'currentMedications','height','weight','bmi','bloodPressureSys',
    'bloodPressureDia','heartRate','typeOfDiet','dietaryFeatures',
    'dietaryAllergies','strongDislikes','workActivity','exerciseFrequency',
    'exerciseTypes','mobilityIssues','mealPrepCapability','appliances',
    'eatingSchedule','eatingScheduleOther','primaryGoals','readinessToChange',
    'weightLossDesired','suggestedCalorieTarget','suggestedCalorieOther',
    'a1c','fastingGlucose','ldl','hdl','triglycerides','totalCholesterol',
    'egfr','creatinine','potassium','uacr','altAst','vitaminD','b12'
  ];

  for (const field of requiredFields) {
    if (!(field in data)) {
      return res.status(422).json({ error: `Missing field: ${field}` });
    }
  }

  // Optionally: Validate types. For brevity, assume front-end sends correct shapes.
  savedProfile = data;
  res.json({ status: 'saved' });
});

const PORT = 8000;
app.listen(PORT, () => console.log(`Backend listening on http://localhost:${PORT}`)); 