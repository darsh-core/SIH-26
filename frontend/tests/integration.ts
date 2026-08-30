import { authApi } from "../src/services/authApi";
import { competencyApi } from "../src/services/competencyApi";
import { recommendationApi } from "../src/services/recommendationApi";
import { learningPlanApi } from "../src/services/learningPlanApi";
import { assessmentApi } from "../src/services/assessmentApi";
import { useAuthStore } from "../src/store/authStore";

// Mock environment for node testing
if (!globalThis.fetch) {
  throw new Error("Node.js v18+ is required to run standard fetch calls.");
}

async function runIntegrationTest() {
  console.log("==================================================");
  console.log("STARTING FRONTEND API INTEGRATION TEST...");
  console.log("==================================================");

  try {
    // 1. Authenticate with seeded credentials
    console.log("\n[STEP 1] Login Verification...");
    const loginData = await authApi.login("employee@mospi.gov.in", "password123");
    console.log("✓ Login successful!");
    console.log(`  Token: ${loginData.access_token.slice(0, 15)}...`);
    
    // Set token in ZUSTAND store memory to allow getMe call to be authenticated
    useAuthStore.getState().setAuth(loginData.access_token, loginData.refresh_token, {} as any);
    
    // Fetch profile
    const userProfile = await authApi.getMe();
    console.log(`  User Designation: ${userProfile.profile?.designation}`);
    
    // Set token in Zustand store memory for base API client authorization header
    useAuthStore.getState().setAuth(loginData.access_token, loginData.refresh_token, userProfile);
    const userId = userProfile.id;

    // 2. Fetch Gaps & Readiness
    console.log("\n[STEP 2] Fetch Competency Gaps & Readiness...");
    const gaps = await competencyApi.getCompetencyGaps(userId);
    console.log("✓ Competency gaps fetched successfully!");
    console.log(`  Designation: ${gaps.role.name}`);
    console.log(`  Role Readiness Score: ${gaps.overall_readiness}%`);
    
    // Find Sampling gap size
    const samplingGap = gaps.gaps.find(g => g.competency_code === "STAT_SAMPLING");
    if (samplingGap) {
      console.log(`  Sampling Methodology Gap: Current ${samplingGap.current_level} -> Required ${samplingGap.required_level} (Gap: -${samplingGap.gap})`);
    }

    // 3. Fetch Recommendations
    console.log("\n[STEP 3] Fetch Recommendations...");
    const recs = await recommendationApi.getRecommendations(userId, { debug: true });
    console.log("✓ Recommendations retrieved successfully!");
    console.log(`  Total courses/programs recommended: ${recs.recommendations.length}`);
    
    if (recs.recommendations.length > 0) {
      const firstRec = recs.recommendations[0];
      console.log(`  Top Recommended: ${firstRec.title} (${firstRec.provider}) - Match Score: ${firstRec.score}%`);
      console.log(`  Explanation: ${firstRec.reason}`);
      if (firstRec.debug_scores) {
        console.log(`  Scoring Breakdown: Competency Match: ${firstRec.debug_scores.competency_match}, Semantic: ${firstRec.debug_scores.semantic_similarity}, Quality: ${firstRec.debug_scores.provider_quality}`);
      }
    }

    // 4. Generate sequenced Learning Plan roadmap
    console.log("\n[STEP 4] Generate Sequenced Learning Plan...");
    const plan = await learningPlanApi.generateLearningPlan(userId);
    console.log("✓ Learning plan created successfully!");
    console.log(`  Plan Title: ${plan.title}`);
    console.log(`  Total journey items: ${plan.items.length}`);

    // 5. Query seeded assessments and simulate attempt submission
    console.log("\n[STEP 5] Run Assessment Submission...");
    const assessments = await assessmentApi.getAssessments();
    const quiz = assessments.items.find(a => a.title.includes("Sampling") || a.title.includes("Core Assessment"));
    
    if (!quiz) {
      console.log("  ⚠️ Skipping quiz submission: No seeded quiz found.");
    } else {
      console.log(`  Found Seeded Quiz: ${quiz.title}`);
      
      // Start attempt session
      const attempt = await assessmentApi.startAttempt(quiz.id);
      console.log(`  ✓ Start attempt created with ID: ${attempt.attempt_id}`);
      
      const questions = attempt.questions || [];
      
      // Prepare mock answer choice selecting correct options based on seeded text
      const answers = questions.map(q => {
        const text = q.text || "";
        console.log(`    Question Text: "${text}"`);
        let selectedOption = q.options[0];
        
        if (text.includes("equal and known chance")) {
          selectedOption = q.options.find((o: any) => (o.text || "").includes("Simple Random")) || selectedOption;
        } else if (text.includes("primary purpose of stratification")) {
          selectedOption = q.options.find((o: any) => (o.text || "").includes("ensure sub-populations")) || selectedOption;
        }
        
        console.log(`    Selected Option Text: "${selectedOption?.text || selectedOption?.option_text}"`);
        return {
          question_id: q.id,
          selected_option_id: selectedOption?.id || ""
        };
      });
      
      // Submit attempt answers
      const result = await assessmentApi.submitAnswers(quiz.id, attempt.attempt_id, answers);
      console.log("✓ Assessment answers evaluated!");
      console.log(`  Verified Score: ${result.score}%`);
      console.log(`  Passed Checkpoint: ${result.is_passed}`);
      
      // Verify level updates dynamically by querying competencies
      const updatedComps = await competencyApi.getUserCompetencies(userId);
      const updatedSampling = updatedComps.find(uc => uc.competency?.code === "STAT_SAMPLING");
      if (updatedSampling) {
        console.log(`  Upgraded Competency Level for STAT_SAMPLING: ${updatedSampling.current_level} (Initial level was 2.3)`);
      }
    }

    // 6. Refresh Recommendations after Assessment Gain
    console.log("\n[STEP 6] Refresh Recommendations post-quiz level gains...");
    const refreshed = await recommendationApi.refreshRecommendations(userId);
    console.log("✓ Recommendations refreshed successfully!");
    console.log(`  Updated count: ${refreshed.recommendations.length}`);
    
    console.log("\n==================================================");
    console.log("✓ ALL API INTEGRATION TESTS PASSED SUCCESSFULLY!");
    console.log("==================================================");
    process.exit(0);

  } catch (err: any) {
    console.error("\n❌ TEST FAILED WITH EXCEPTION:");
    console.error(err.message);
    if (err.data) {
      console.error(JSON.stringify(err.data, null, 2));
    }
    process.exit(1);
  }
}

runIntegrationTest();
