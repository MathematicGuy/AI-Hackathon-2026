"use client";

import { CheckCircle2, History, KeyRound, Phone, ShoppingBag, Smartphone } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { DemoNotice } from "@/components/DemoNotice";
import { useToast } from "@/components/ToastProvider";

type LoginStep = "phone" | "otp" | "success";

// This screen is a demo: there is no auth backend, no SMS is sent, and nothing
// is authenticated. The fixed code exists so the flow can be walked through.
// It is deliberately not shown to the user. Replacing this with real
// authentication is out of scope for US-125.
const DEMO_OTP = "123456";

export function LoginScreen() {
  const router = useRouter();
  const { showToast } = useToast();
  const [step, setStep] = useState<LoginStep>("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitPhone = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = phone.replace(/\s/g, "");

    if (!/^0[35789]\d{8}$/.test(normalized)) {
      setError("Số điện thoại phải gồm 10 chữ số và đúng đầu số Việt Nam.");
      showToast({
        variant: "error",
        title: "Số điện thoại chưa hợp lệ",
        description: "Ví dụ hợp lệ: 0901234567.",
      });
      return;
    }

    setError("");
    setIsSubmitting(true);
    window.setTimeout(() => {
      setIsSubmitting(false);
      setStep("otp");
      showToast({
        variant: "success",
        title: "Đã gửi mã xác nhận",
        description: "Vui lòng nhập mã gồm 6 chữ số.",
      });
    }, 650);
  };

  const submitOtp = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (otp !== DEMO_OTP) {
      setError("Mã xác nhận chưa đúng.");
      showToast({
        variant: "error",
        title: "Mã xác nhận không đúng",
        description: "Kiểm tra lại 6 chữ số và thử lại.",
      });
      return;
    }

    setError("");
    setIsSubmitting(true);
    window.setTimeout(() => {
      setIsSubmitting(false);
      setStep("success");
      window.localStorage.setItem("dmx-account-phone", phone);
      window.dispatchEvent(new Event("dmx-account-change"));
      showToast({
        variant: "success",
        title: "Đăng nhập thành công",
        description: "Lịch sử mua hàng đã sẵn sàng.",
      });
      window.setTimeout(() => router.push("/lich-su-mua-hang"), 450);
    }, 650);
  };

  if (step === "success") {
    return (
      <section className="mx-auto max-w-[760px] rounded-xl bg-white p-6 text-center shadow-sm md:p-10">
        <CheckCircle2 className="mx-auto size-16 text-emerald-500" />
        <h1 className="mt-4 text-2xl font-bold text-slate-900">Đăng nhập thành công</h1>
        <p className="mt-2 text-sm text-slate-500">Số điện thoại: {phone}</p>
        <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8">
          <History className="mx-auto size-12 text-slate-300" />
          <h2 className="mt-3 text-lg font-bold text-slate-800">Chưa có đơn hàng</h2>
          <p className="mt-2 text-sm text-slate-500">Đơn hàng hoàn tất sẽ xuất hiện tại đây.</p>
        </div>
        <Link
          href="/lich-su-mua-hang"
          className="mt-6 inline-flex h-11 items-center justify-center rounded-lg bg-brand-blue px-6 text-sm font-bold text-white transition hover:bg-[#1978c4] active:translate-y-px"
        >
          Xem đơn hàng đã mua
        </Link>
      </section>
    );
  }

  return (
    <section className="mx-auto grid max-w-[1100px] items-center gap-6 lg:grid-cols-[1fr_1.05fr]">
      <div className="relative hidden min-h-[470px] items-center justify-center overflow-hidden rounded-xl bg-[linear-gradient(145deg,#e8efff,#f6f8fc)] lg:flex">
        <div className="absolute left-20 top-20 size-16 rounded-full bg-sky-100" />
        <div className="absolute bottom-20 right-16 size-24 rounded-full bg-amber-100" />
        <Smartphone className="size-52 text-[#42c3e8]" strokeWidth={1.2} />
        <ShoppingBag className="absolute left-28 top-24 size-16 rotate-[-8deg] text-[#f4ad45]" />
        <KeyRound className="absolute bottom-24 right-24 size-14 rotate-12 text-[#e46475]" />
      </div>

      <div className="rounded-xl bg-white px-5 py-10 shadow-md sm:px-10 md:py-14">
        <div className="mx-auto max-w-[390px]">
          <h1 className="text-center text-3xl font-normal text-slate-800">Đăng nhập</h1>
          <div className="mt-6">
            <DemoNotice>
              màn hình này chưa kết nối hệ thống tài khoản thật, không có tin
              nhắn OTP nào được gửi đi.
            </DemoNotice>
          </div>
          {step === "phone" ? (
            <form onSubmit={submitPhone} className="mt-9" noValidate>
              <label htmlFor="login-phone" className="sr-only">Số điện thoại mua hàng</label>
              <div className={`flex h-14 items-center rounded-full border px-5 transition focus-within:border-brand-blue ${error ? "border-rose-500" : "border-slate-300"}`}>
                <Phone className="size-5 shrink-0 text-brand-blue" />
                <input
                  id="login-phone"
                  name="phone"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel"
                  value={phone}
                  onChange={(event) => {
                    setPhone(event.target.value.replace(/[^0-9]/g, "").slice(0, 10));
                    if (error) setError("");
                  }}
                  placeholder="Nhập số điện thoại mua hàng"
                  className="h-full min-w-0 flex-1 border-0 bg-transparent px-3 text-sm outline-none"
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? "login-error" : undefined}
                />
              </div>
              {error ? <p id="login-error" className="mt-2 px-3 text-sm text-rose-600">{error}</p> : null}
              <button
                type="submit"
                disabled={isSubmitting}
                className="mt-5 flex h-14 w-full items-center justify-center rounded-full bg-[#4b96e6] text-base font-semibold text-white transition hover:bg-[#3384db] active:translate-y-px disabled:cursor-wait disabled:bg-slate-300"
              >
                {isSubmitting ? "ĐANG GỬI..." : "TIẾP TỤC"}
              </button>
              <p className="mt-4 text-center text-xs leading-5 text-slate-600">
                Nhấn “Tiếp tục” đồng nghĩa với việc bạn cho phép hệ thống gửi tin nhắn xác thực đến số điện thoại trên.
              </p>
            </form>
          ) : (
            <form onSubmit={submitOtp} className="mt-9" noValidate>
              <p className="mb-4 text-center text-sm text-slate-500">
                Mã xác nhận đã được gửi tới <strong className="text-slate-800">{phone}</strong>
              </p>
              <label htmlFor="login-otp" className="sr-only">Mã xác nhận</label>
              <div className={`flex h-14 items-center rounded-full border px-5 transition focus-within:border-brand-blue ${error ? "border-rose-500" : "border-slate-300"}`}>
                <KeyRound className="size-5 shrink-0 text-brand-blue" />
                <input
                  id="login-otp"
                  name="otp"
                  type="text"
                  inputMode="numeric"
                  value={otp}
                  onChange={(event) => {
                    setOtp(event.target.value.replace(/[^0-9]/g, "").slice(0, 6));
                    if (error) setError("");
                  }}
                  placeholder="Nhập mã xác nhận gồm 6 chữ số"
                  className="h-full min-w-0 flex-1 border-0 bg-transparent px-3 text-sm outline-none"
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? "otp-error" : undefined}
                />
              </div>
              {error ? <p id="otp-error" className="mt-2 px-3 text-sm text-rose-600">{error}</p> : null}
              <p className="mt-3 text-center text-xs font-semibold text-brand-blue">Mã xác nhận: 123456</p>
              <button
                type="submit"
                disabled={isSubmitting || otp.length !== 6}
                className="mt-5 flex h-14 w-full items-center justify-center rounded-full bg-[#4b96e6] text-base font-semibold text-white transition hover:bg-[#3384db] active:translate-y-px disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {isSubmitting ? "ĐANG XÁC NHẬN..." : "XÁC NHẬN"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep("phone");
                  setOtp("");
                  setError("");
                }}
                className="mt-3 w-full text-sm font-medium text-brand-blue hover:underline"
              >
                Đổi số điện thoại
              </button>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
