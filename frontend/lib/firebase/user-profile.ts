import {
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
  type Timestamp,
} from "firebase/firestore";
import { getFirestore } from "firebase/firestore";
import { getApp } from "firebase/app";
import type { User } from "firebase/auth";

export type UserPreferences = {
  roleFocus: string;
  preferredLocation: string;
  keywords: string[];
};

export type UserProfile = {
  uid: string;
  email: string | null;
  displayName: string | null;
  fullName: string;
  photoURL: string | null;
  onboardingCompleted: boolean;
  onboardingStep: number;
  preferences: UserPreferences;
  createdAt: Timestamp | null;
  updatedAt: Timestamp | null;
};

function getDb() {
  return getFirestore(getApp());
}

export async function getUserProfile(uid: string): Promise<UserProfile | null> {
  const snap = await getDoc(doc(getDb(), "users", uid));
  if (!snap.exists()) return null;
  return snap.data() as UserProfile;
}

export async function upsertUserProfile(user: User): Promise<UserProfile | null> {
  const ref = doc(getDb(), "users", user.uid);
  const snap = await getDoc(ref);

  if (snap.exists()) {
    return snap.data() as UserProfile;
  }

  const profile: UserProfile = {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName,
    fullName: user.displayName ?? "",
    photoURL: user.photoURL,
    onboardingCompleted: false,
    onboardingStep: 1,
    preferences: {
      roleFocus: "",
      preferredLocation: "",
      keywords: [],
    },
    createdAt: serverTimestamp() as Timestamp,
    updatedAt: serverTimestamp() as Timestamp,
  };

  await setDoc(ref, profile);
  return profile;
}

export async function completeUserOnboarding(
  user: User,
  data: { fullName: string; preferences: UserPreferences },
): Promise<void> {
  const ref = doc(getDb(), "users", user.uid);
  await setDoc(
    ref,
    {
      fullName: data.fullName,
      preferences: data.preferences,
      onboardingCompleted: true,
      onboardingStep: 3,
      updatedAt: serverTimestamp(),
    },
    { merge: true },
  );
}
